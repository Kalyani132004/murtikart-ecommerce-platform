from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from admin_app.models import Product, Discount, Order, OrderItem, Payment, Invoice, Discount
import json
from django.db.models import Q

@login_required
def dashboard(request):
    print('customer role section: ',request.user.role)
    # user orders use request.user  
    user_orders = Order.objects.filter(user=request.user)
    total_orders_count = user_orders.count()

    # user order is_active chya aivaji aopn visibility use keli aahe 
    # those model available for wholesaler or both filter them 
    available_models_count = Product.objects.filter(visibility__in=['wholesaler', 'both']).count()

    # remaining payment
    total_amount = user_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    paid_amount = user_orders.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    pending_payment = total_amount - paid_amount

    # current discount (Discount model use  discount_percent) 
    latest_offer = Discount.objects.all().order_by('-discount_percent').first()
    discount_text = f"{latest_offer.discount_percent}% OFF" if latest_offer else "0% OFF"

    # recent 5 orders 
    recent_orders = user_orders.order_by('-date')[:5]

    context = {
        'total_orders': total_orders_count,
        'available_models': available_models_count,
        'pending_payment': pending_payment,
        'discount_text': discount_text,
        'recent_orders': recent_orders,
    }
    return render(request, 'wholesaler/index.html',context)

@login_required
def models(request):
    
    products = Product.objects.filter(
                Q(visibility='wholesaler') | Q(visibility='both')
            )
    products_list = []
    for p in products:
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
    products_json = json.dumps(products_list)
    return render(request, 'wholesaler/models.html', {
        'products': products,
        'products_json': products_json
    })

# @login_required
# def billing(request):
#     """Wholesaler Order Request System - Wholesaler selects models and sends order to admin."""
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             items = data.get('items', [])
#             total_amount = float(data.get('total_amount', 0))
#             note = data.get('note', '')
#             status = data.get('status', 'pending') # Handle 'draft' or 'pending'

#             if not items:
#                 return JsonResponse({'status': 'error', 'message': 'No items selected.'}, status=400)

#             order = Order.objects.create(
#                 user=request.user,
#                 created_by=request.user,
#                 total_amount=total_amount,
#                 paid_amount=0,
#                 status=status,
#                 delivery_address=note
#             )

#             for item in items:
#                 # Find product by model number (matches JS autocomplete)
#                 model_number = item.get('model_number')
#                 product = Product.objects.filter(model_number=model_number).first()
#                 if product:
#                     OrderItem.objects.create(
#                         order=order,
#                         product=product,
#                         quantity=int(item.get('qty', 1)),
#                         price=float(product.price)
#                     )

#             # Record initial payment (even for drafts)
#             Payment.objects.create(
#                 order=order,
#                 total_amount=total_amount,
#                 paid=0,
#                 pending=total_amount
#             )

#             return JsonResponse({'status': 'success', 'order_id': order.id, 'status_saved': status})

#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

#     products = Product.objects.all().order_by('model_number')
#     products_json = json.dumps([{
#         'model_number': p.model_number,
#         'name': p.name,
#         'price': float(p.price) if p.price else 0,
#         'stock': p.stock if p.stock else 0,
#         'image': p.image.url if p.image else '/static/assets/images/dagdusheth_gold.png'
#     } for p in products])

#     return render(request, 'wholesaler/billing.html', {
#         'products': products,
#         'products_json': products_json,
#         'user': request.user
#     })

@login_required
def orders(request):
    """Show this wholesaler's submitted orders from DB."""
    my_orders = Order.objects.filter(
        user=request.user
    ).prefetch_related('items__product').order_by('-date')
    return render(request, 'wholesaler/orders.html', {'orders': my_orders})

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
   
from django.db.models import Sum


from django.db.models import Sum, Q
@login_required
def invoices(request):
    orders = request.user.order_set.all().prefetch_related('items__product')
    
    grand_total = 0
    total_discount_amt = 0
    total_paid = orders.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0

    for order in orders:
        # 1. Order cha subtotal calculate kara
        subtotal = order.total_amount 
        
        # 2. Discount shodha
        tier = Discount.objects.filter(
            min_price__lte=subtotal
        ).filter(
            Q(max_price__gte=subtotal) | Q(max_price__isnull=True)
        ).order_by('-discount_percent').first()

        # 3. Calculation logic
        if tier:
            order.disc_per = tier.discount_percent
            order.disc_amt = (subtotal * tier.discount_percent) / 100
        else:
            order.disc_per = 0
            order.disc_amt = 0
        
        order.real_amount = subtotal - order.disc_amt
        
        # Totals update kara
        grand_total += subtotal
        total_discount_amt += order.disc_amt

    final_payable = grand_total - total_discount_amt
    total_balance = final_payable - total_paid

    context = {
        'orders': orders,
        'grand_total': grand_total,
        'total_discount': total_discount_amt,
        'final_payable': final_payable,
        'total_paid': total_paid,
        'total_balance': total_balance,
    }
    return render(request, 'wholesaler/invoices.html', context)

@login_required
def my_orders(request):
    #arrange orders in new to old orders
    orders = request.user.order_set.all().prefetch_related('items__product').order_by('-date')
    return render(request, 'wholesaler/my_orders.html', {'orders': orders})

@login_required
def edit_order(request, order_id):
    """Edit a pending wholesale order."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        if order.status not in ['pending', 'draft']:
            return JsonResponse({'status': 'error', 'message': 'Only pending or draft orders can be edited.'}, status=400)
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            note = data.get('note', order.delivery_address or '')
            status = data.get('status', order.status) # Maintain current status or update to 'pending'/'draft'

            if not items:
                return JsonResponse({'status': 'error', 'message': 'No items selected.'}, status=400)

            # Replace all items
            order.items.all().delete()
            total = 0
            for item in items:
                model_number = item.get('model_number')
                product = Product.objects.filter(model_number=model_number).first()
                if product:
                    qty = int(item.get('qty', 1))
                    price = float(product.price)
                    OrderItem.objects.create(order=order, product=product, quantity=qty, price=price)
                    total += price * qty

            order.total_amount = total
            order.delivery_address = note
            order.status = status
            order.save()

            # Update payment record
            payment = Payment.objects.filter(order=order).first()
            if payment:
                payment.total_amount = total
                payment.pending = max(0, float(total) - float(payment.paid))
                payment.save()

            return JsonResponse({'status': 'success', 'order_id': order.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # GET - allow viewing any order, but JS will handle disabling edits if not pending/draft
    # if order.status != 'pending':
    #     return redirect('wholesaler:orders')

    products = Product.objects.all().order_by('model_number')
    products_json = json.dumps([{
        'model_number': p.model_number,
        'name': p.name,
        'price': float(p.price) if p.price else 0,
        'stock': p.stock if p.stock else 0,
        'image': p.image.url if p.image else '/static/assets/images/dagdusheth_gold.png'
    } for p in products])

    existing_items = {}
    for item in order.items.all():
        existing_items[item.product.model_number] = item.quantity

    return render(request, 'wholesaler/edit_order.html', {
        'order': order,
        'products': products,
        'products_json': products_json,
        'existing_items_json': json.dumps(existing_items),
        'user': request.user
    })

@login_required
def offers(request):
    offers = Discount.objects.all().order_by('min_price')
    return render(request, 'wholesaler/offers.html', {'offers': offers})
    
@login_required
def profile(request):
    user = request.user
    
    if request.method == 'POST':
        # get data 
        full_name = request.POST.get('full_name')
        mobile = request.POST.get('mobile')
        business_name = request.POST.get('business_name')
        address = request.POST.get('address')
        profile_pic = request.FILES.get('profile_pic') 

        # update details in user model
        user.full_name = full_name
        user.mobile = mobile
        user.address = address
        
        # if model have bussiness_name field used this 
        if hasattr(user, 'business_name'):
            user.business_name = business_name
            
        # if update profile use this 
        if profile_pic:
            user.profile_img = profile_pic 

        user.save()
        messages.success(request, "Profile Updated Successfully!")
        return redirect('wholesaler:profile') #profile url

    return render(request, 'wholesaler/profile.html')