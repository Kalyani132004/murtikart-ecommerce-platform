from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from admin_app.models import Product, Order, OrderItem, Payment, Invoice,  Discount
from django.utils import timezone
from django.contrib import messages
import json

from django.db.models import Sum, F, Q
from django.http import HttpResponse, JsonResponse

@login_required
def dashboard(request):
    print('customer role section: ',request.user.role)
    # fetch the current user order
    user_orders = Order.objects.filter(user=request.user).order_by('-date')
    
    # get the total bookings 
    total_bookings = user_orders.count()
    
    #  Available Models for current user visibility
    # filter the type 'customer' or 'both' 
    available_models = Product.objects.filter(
        visibility__in=['customer', 'both'], 
        stock__gt=0
    ).count()
    
    # Pending Payments
    # total amt and paid amt
    pending_data = user_orders.aggregate(
        total_pending=Sum(F('total_amount') - F('paid_amount'))
    )
    total_pending = pending_data['total_pending'] or 0

    # dashboard shown the recent 5 bookings 
    # use 'prefetch_related' because 1 or more items easily shown 
    recent_bookings = user_orders.prefetch_related('items__product')[:5]

    context = {
        'total_bookings_count': total_bookings,
        'available_models_count': available_models,
        'total_pending_balance': total_pending,
        'recent_bookings': recent_bookings,
    }
    
    #return render(request, 'customer/dashboard.html', context)
    return render(request, 'customer/index.html',context)

@login_required
def models(request):
    #products = Product.objects.all()
    #fetch the model this model visibility is 'both' or 'customer'
    products = Product.objects.filter(
                Q(visibility='customer') | Q(visibility='both')
            )
    products_list = []
    for p in products:
        # model_type raw choices: 'decorated' or 'color'
        # Map to display values that match the template filters
        type_map = {'decorated': 'Decorated', 'color': 'Color'}
        products_list.append({
            'id': p.model_number,
            'name': p.name,
            'type': type_map.get(p.model_type, p.get_model_type_display()),
            'size': float(p.size) if p.size else 0,
            'price': float(p.price) if p.price else 0,
            'stock': p.stock if p.stock else 0,
            'image': p.image.url if p.image else '/static/assets/images/dagdusheth_gold.png'
        })
    # Use json.dumps for safe JSON serialization (avoids Django template escaping issues)
    products_json = json.dumps(products_list)
    return render(request, 'customer/models.html', {
        'products': products,
        'products_json': products_json
    })

#check model book validation
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
    # Get ID from URL (e.g., ?id=101)
    book_id = request.GET.get('id')
    
    # 1. Fetch products for the dropdown
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
        
            # 1. Calculate Initial Subtotal (Using Decimal)
            subtotal = product.price * Decimal(quantity)
            
            # 2. Secure Backend Discount Calculation
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
            
    # required for: Frontend JS 
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
@login_required
def bookings(request):
    # If 'orderitem_set' is giving an error, try fetching just the orders first
    # to see if the page loads. 
    orders = Order.objects.filter(user=request.user).order_by('-id')
    return render(request, 'customer/bookings.html', {'orders': orders})
    
from decimal import Decimal
@login_required
def invoices(request):
    # with the help of prefetch_related easily gets the product price वापरल्यामुळे product ची किंमत लगेच मिळेल
    orders = request.user.order_set.all().prefetch_related('items__product').order_by('-id')
    
    for order in orders:
        # fetch the actual price (4200 * 3 = 12600)
        # sometimes item.price have the discount price so i used the item.product.price 
        gross = sum(item.product.price * item.quantity for item in order.items.all())
        
        # join this variables on Order object
        order.calculated_gross = Decimal(str(gross))
        order.calculated_disc = order.calculated_gross - Decimal(str(order.total_amount))
        
        # if discount is less than 0 so set the 0
        if order.calculated_disc < 0:
            order.calculated_disc = Decimal('0.00')

    return render(request, 'customer/invoices.html', {'orders': orders})

@login_required
def offers(request):
    offers = Discount.objects.all().order_by('min_price')
    return render(request, 'customer/offers.html', {'offers': offers})

@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        # update user model info 
        full_name = request.POST.get('full_name')
        user.full_name = full_name # full name field 
        
        # name split and save in django defoult field 
        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        user.mobile = request.POST.get('mobile')
        user.address = request.POST.get('address')
        
        #  manage profile image 
        if 'profile_pic' in request.FILES:
            user.profile_img = request.FILES['profile_pic']
            
        user.save()
        messages.success(request, "Update details successfully")
        return redirect('customer:profile')

    return render(request, 'customer/profile.html', {'user': user})
    