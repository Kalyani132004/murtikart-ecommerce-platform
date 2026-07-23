from admin_app.models import *
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
import json

def check_validation(request):
    # Log incoming data for debugging
    if request.method == "POST":
        # 1. Capture the ID exactly as it comes from the frontend ('MK-1')
        product_id = request.POST.get('model_id')
        
        try:
            # 2. Convert inputs to integers safely
            # We use a default of '0' to avoid errors if the field is empty
            qty_val = request.POST.get('quantity', '0')
            adv_val = request.POST.get('advance_paid', '0')
            
            
            requested_qty = int(qty_val)
            advance_paid = int(adv_val)

            # 3. Fetch the product. 
            # IMPORTANT: If your DB ID is an integer, use the field name 
            # that stores 'MK-1' (e.g., product_code or sku) instead of 'id'.
            # If 'id' IS the field that holds 'MK-1', this line is fine.
            product = Product.objects.get(model_number=product_id)
            
            # --- VALIDATION LOGIC ---
            
            # Stock Check
            if requested_qty > product.stock:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Insufficient stock. Only {product.stock} items left.'
                })
            
            # Calculation (calculated on backend for security)
            total_price = product.price * requested_qty
            
            # Advance amount logic
            if advance_paid >= total_price:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Advance (₹{advance_paid}) cannot be more than the total price (₹{total_price}).'
                })
            
            if advance_paid < 500:
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

@login_required
def book(request):
    # Get ID from URL (e.g., ?id=101)
    book_id = request.GET.get('id')
    
    # 1. Fetch products for the dropdown and the specific model for validation
    products = Product.objects.filter(visibility__in=['wholesaler', 'both'])
    
    # Use get_object_or_404 to prevent crashes if ID is missing or wrong
    actual_model = get_object_or_404(Product, model_number=book_id) if book_id else None
    
    discounts = Discount.objects.all().order_by('min_price')

    if request.method == 'POST':
        # Use the ID from the POST data (fallback to URL param)
        selected_model_id = request.POST.get('model_id', book_id)
        quantity = int(request.POST.get('quantity', 1))
        advance_paid = float(request.POST.get('advance_paid', 0))
        address = request.POST.get('address')
        delivery_date = request.POST.get('delivery_date')
        try:
            # Refresh product instance to get latest stock/price
            product = Product.objects.get(model_number=selected_model_id)
        
            # 1. Calculate Initial Subtotal
            subtotal = float(product.price) * quantity
            
            # 2. Secure Backend Discount Calculation
            # We look for a tier where subtotal fits between min and max
            discount_tier = Discount.objects.filter(min_price__lte=subtotal).filter(
                Q(max_price__gte=subtotal) | Q(max_price__isnull=True)
            ).order_by('-discount_percent').first()
            
            discount_amount = 0
            if discount_tier:
                discount_amount = (subtotal * discount_tier.discount_percent) / 100
            
            final_total = subtotal - discount_amount
            
            # 3. Database Transaction (Atomic)
            # Create Order
            order = Order.objects.create(
                user=request.user,
                total_amount=final_total,
                paid_amount=advance_paid,
                status='pending',
                delivery_address=address,
                delivery_date=delivery_date if delivery_date else None
            )
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price 
            )
            
            Payment.objects.create(
                order=order,
                total_amount=final_total,
                paid=advance_paid,
                pending=final_total - advance_paid
            )
            
            Invoice.objects.create(
                order=order,
                user=request.user
            )

            # Reduce Stock after successful booking
            product.stock -= quantity
            product.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Booking Successful! Your order has been placed.',
                'redirect_url': reverse('wholesaler:orders')
            })
            
        except Product.DoesNotExist as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e) # Or a custom error message
            }, status=400)
            
    # Data for JS
    products_list = [{'id': p.model_number, 'name': p.name, 'price': float(p.price)} for p in products]
    discounts_list = [
        {'min_price': float(d.min_price), 
         'max_price': float(d.max_price) if d.max_price else 9999999, 
         'discount_percent': d.discount_percent} 
        for d in discounts
    ]
        
    return render(request, 'wholesaler/book.html', {
        'products': products,
        'actual_model': actual_model, # Pass this to auto-select in template
        'products_list': products_list,
        'discounts_json': json.dumps(discounts_list)
    })