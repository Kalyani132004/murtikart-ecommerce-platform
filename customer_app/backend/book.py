from admin_app.models import *
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
from django.shortcuts import render,get_object_or_404
from django.urls import reverse
from django.db.models import Q

#check model book validation
def check_validation(request):
    # Log incoming data for debugging
    if request.method == "POST":
        # Capture the ID exactly as it comes from the frontend 'MK-1'
        product_id = request.POST.get('model_id')
        
        try:
            # Convert inputs to integers safely
            # We use a default of '0' to avoid errors if the field is empty
            qty_val = request.POST.get('quantity', '0')
            adv_val = request.POST.get('advance_paid', '0')
            
            
            requested_qty = int(qty_val)
            advance_paid = int(adv_val)

            # 3. Fetch the product. 
            
            product = Product.objects.get(model_number=product_id)
            
            #validation logic
            
            # Stock Check
            if requested_qty > product.stock:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Insufficient stock. Only {product.stock} items left.'
                })
            
            # Calculation 
            total_price = product.price * requested_qty
            
            # Advance amount logic
            if advance_paid > total_price:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Advance (₹{advance_paid}) cannot be more than the total price (₹{total_price}).'
                })
            
            if advance_paid < 500 and not product.price < 500:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Please pay at least ₹500 as an advance.'
                })
                

            # If everything is perfect
            
            return JsonResponse({'status': 'success'})

        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': f'Product {product_id} not found in database.'})
        except ValueError as e:
            # This will show you exactly what value caused the crash
            return JsonResponse({
                'status': 'error', 
                'message': f'Value Error: {str(e)} | Qty received: {request.POST.get("quantity")} | Adv received: {request.POST.get("advance_paid")}'
            })
        except Exception as e:
            # Catch-all for unexpected errors
            return JsonResponse({'status': 'error', 'message': f'System error: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Invalid Request Method'})
from decimal import Decimal
@login_required
def book(request):
    # Get ID from url
    book_id = request.GET.get('id')
    
    # Fetch products for the dropdown
    products = Product.objects.filter(visibility__in=['customer', 'both'])
    
    # Use get_object_or_404 to prevent crashes if ID is missing or wrong
    actual_model = get_object_or_404(Product, model_number=book_id) if book_id else None
    
    discounts = Discount.objects.all().order_by('min_price')

    if request.method == 'POST':
        # Use the ID from the POST data (fallback to URL param)
        selected_model_id = request.POST.get('model_id', book_id)
        
        try:
            quantity = int(request.POST.get('quantity', 1))
            # use Decimal for amount  
            advance_paid = Decimal(request.POST.get('advance_paid', 0) or '0')
            address = request.POST.get('address')
            delivery_date = request.POST.get('delivery_date')

            # Refresh product instance to get latest stock/price
            product = Product.objects.get(model_number=selected_model_id)
        
            #  Calculate Initial Subtotal (Using Decimal)
            subtotal = product.price * Decimal(quantity)
            
            # Secure Backend Discount Calculation
            #  check the subtotal is bigger than min_price and smaller than max_price 
            discount_tier = Discount.objects.filter(
                min_price__lte=subtotal
            ).filter(
                Q(max_price__gte=subtotal) | Q(max_price__isnull=True)
            ).order_by('-discount_percent').first()
            
            discount_amount = Decimal('0.00')
            if discount_tier:
                discount_amount = (subtotal * Decimal(discount_tier.discount_percent)) / Decimal('100')
            
            # finel total less dicount 
            final_total = subtotal - discount_amount
            
            # write Database Transaction
            # Create Order
            order = Order.objects.create(
                user=request.user,
                total_amount=final_total,
                paid_amount=advance_paid,
                status='pending',
                delivery_address=address,
                delivery_date=delivery_date if delivery_date else None
            )
            
            # save the actual price on Order Item
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price 
            )
            
            # update the payment record 
            Payment.objects.create(
                order=order,
                total_amount=final_total,
                paid=advance_paid,
                pending=final_total - advance_paid
            )
            
            # generate invoice 
            Invoice.objects.create(
                order=order,
                user=request.user
            )

            # less the stock 
            product.stock -= quantity
            product.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Booking Successful! Discount of ₹{discount_amount} applied.',
                'redirect_url': reverse('customer:bookings')
            })
            
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    # required for js 
    products_list = [{'id': p.model_number, 'name': p.name, 'price': float(p.price)} for p in products]
    discounts_list = [
        {
            'min_price': float(d.min_price), 
            'max_price': float(d.max_price) if d.max_price else 9999999, 
            'discount_percent': d.discount_percent
        } for d in discounts
    ]
        
    return render(request, 'customer/book.html', {
        'products': products,
        'actual_model': actual_model,
        'products_list': products_list,
        'discounts_json': json.dumps(discounts_list),
    })  