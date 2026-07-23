from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse,HttpResponse
from .models import Product, Order, OrderItem, Payment, Invoice, User
import json
from django.core.serializers import serialize

from django.db.models import Sum, F
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view

@login_required
def dashboard(request):
    # without admin all users count 
    customer_count = User.objects.filter(role='customer').count()
    wholesaler_count = User.objects.filter(role='wholesaler').count()
    total_products = Product.objects.count()
    
    # fetch all orders forgot draft
    all_orders = Order.objects.exclude(status='draft')
    
    # Total Bookings 
    total_bookings = all_orders.count()
    
    # Financials
    financials = all_orders.aggregate(
        total_rev=Sum('total_amount'),
        total_p=Sum('paid_amount')
    )
    
    total_revenue = financials['total_rev'] or 0
    total_paid = financials['total_p'] or 0
    pending_balance = total_revenue - total_paid
    
    # ५. Recent Bookings top 10
    all_bookings = all_orders.select_related('user').prefetch_related('items__product').order_by('-date')[:10]

    context = {
        'customer_count': customer_count,
        'wholesaler_count': wholesaler_count,
        'total_models': total_products,
        'total_bookings': total_bookings,
        'pending_balance': pending_balance,
        'all_bookings': all_bookings,
    }
    
    return render(request, 'custom_admin/index.html', context)

def models(request):
    all_models = Product.objects.all()
    all_models_json = serialize('json', all_models)

    return render(request, 'custom_admin/models.html', {
        'all_models': all_models,
        'all_models_json': all_models_json
})
def add_model(request):
    return render(request,'custom_admin/add-model.html')

def customers(request):
    # Fetch all users with the role 'customer'
    customer_list = User.objects.filter(role='customer').order_by('-date_joined')
    return render(request, 'custom_admin/customers.html', {'customers': customer_list})
#add new ganpati models in db

from .models import Product
from .serializers import ProductSerializer

# save the new model 
@api_view(['POST'])
def save_models(request):
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"msg": "Model saved successfully"})
    return Response(serializer.errors)

import json
from rest_framework.decorators import api_view
from rest_framework.response import Response

# set the vissibility status
@api_view(['POST'])
def visibility_check(request):
    try:
        data = request.data
        role = data.get('role')          # 'customer' or 'wholesaler'
        model_id = data.get('modelid')
        is_checked = data.get('is_checked') # True or False

        product = Product.objects.get(model_number=model_id)
        current = product.visibility
        new_visibility = current

        if role == 'customer':
            if is_checked:
                # If turning customer ON, check if wholesaler is already ON
                new_visibility = 'both' if current == 'wholesaler' else 'customer'
            else:
                # If turning customer OFF, check if it was 'both'
                new_visibility = 'wholesaler' if current == 'both' else 'none'

        elif role == 'wholesaler':
            if is_checked:
                # If turning wholesaler ON, check if customer is already ON
                new_visibility = 'both' if current == 'customer' else 'wholesaler'
            else:
                # If turning wholesaler OFF, check if it was 'both'
                new_visibility = 'customer' if current == 'both' else 'none'

        # Update the database
        product.visibility = new_visibility
        product.save()

        return Response({"msg": f"Updated to {new_visibility}"}, status=200)

    except Product.DoesNotExist:
        return Response({"msg": "Product not found"}, status=404)
    except Exception as e:
        return Response({"msg": str(e)}, status=500)
    

from django.shortcuts import render
from .models import Order

def bookings_list(request):
    # Fetch all orders, newest first
    # prefetch_related('items__product') helps get product names without extra queries
    all_bookings = Order.objects.all().select_related('user').prefetch_related('items__product').order_by('-date')
    return render(request, 'custom_admin/bookings.html', {'bookings': all_bookings})

def wholesalers(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        action = request.POST.get('action')
        try:
            order = Order.objects.get(id=order_id)
            if action == 'confirm':
                order.status = 'confirmed'
                order.save()
            elif action == 'cancel':
                order.status = 'cancelled'
                order.save()
            elif action == 'deliver':
                order.status = 'delivered'
                order.save()
        except Order.DoesNotExist:
            pass
        return redirect('admin_panel:wholesalers')

    # Show all wholesale orders (except drafts)
    wholesale_orders = Order.objects.filter(
        user__role='wholesaler'
    ).exclude(status='draft').select_related('user').prefetch_related('items__product').order_by('-date')
    wholesaler_users = User.objects.filter(role='wholesaler')
    return render(request, 'custom_admin/wholesalers.html', {
        'wholesale_orders': wholesale_orders,
        'wholesaler_users': wholesaler_users,
    })

def edit_wholesale_order(request, order_id):
    """Admin edits / updates a wholesale order."""
    order = get_object_or_404(Order, id=order_id, user__role='wholesaler')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            note = data.get('note', order.delivery_address or '')
            status = data.get('status', order.status)

            if not items:
                return JsonResponse({'status': 'error', 'message': 'No items selected.'}, status=400)

            # Replace all items
            order.items.all().delete()
            total = 0
            for item in items:
                product = Product.objects.filter(model_number=item.get('model_number')).first()
                if product:
                    qty = int(item.get('qty', 1))
                    price = float(product.price)
                    OrderItem.objects.create(order=order, product=product, quantity=qty, price=price)
                    total += price * qty

            order.total_amount = total
            order.delivery_address = note
            order.status = status
            order.save()

            payment = Payment.objects.filter(order=order).first()
            if payment:
                payment.total_amount = total
                payment.pending = max(0, total - float(payment.paid))
                payment.save()

            return JsonResponse({'status': 'success', 'order_id': order.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # GET - load edit page
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

    return render(request, 'custom_admin/edit_wholesale_order.html', {
        'order': order,
        'products': products,
        'products_json': products_json,
        'existing_items_json': json.dumps(existing_items),
    })
# def discounts(request):
#     return render(request,'custom_admin/discounts.html')
#discount new code 
from django.shortcuts import render, redirect 
from .models import Discount
from django.contrib import messages

def discount_list(request):
    discounts = Discount.objects.all().order_by('min_price')
    return render(request, 'custom_admin/discounts.html', {'discounts': discounts})

def add_discount(request):
    if request.method == "POST":
        tier_name = request.POST.get('tier_name')
        min_price = request.POST.get('min_price')
        max_price = request.POST.get('max_price')
        discount_percent = request.POST.get('discount_percent')

        Discount.objects.create(
            tier_name=tier_name,
            min_price=min_price,
            max_price=max_price,
            discount_percent=discount_percent
        )
        messages.success(request, "New discount tier added successfully!")
        return redirect('admin_panel:discount_list')

def delete_discount(request, pk):
    if request.method == "POST":
        discount = Discount.objects.get(pk=pk)
        discount.delete()
        messages.warning(request, "Discount tier removed.")
        
        return redirect('admin_panel:discount_list')
#discount new code end 

def billing(request):
    if request.method == 'POST':
        import json
        from django.http import JsonResponse
        from .models import Order, OrderItem, Payment, Invoice, User
        
        try:
            data = json.loads(request.body)
            customer_name = data.get('customer_name')
            customer_mobile = data.get('customer_mobile')
            customer_address = data.get('customer_address')
            items = data.get('items', [])
            total_amount = float(data.get('total_amount', 0))
            advance_paid = float(data.get('advance_paid', 0))
            
            # Find or create a guest customer user
            # Usually we'd want to link to an existing user, but for quick billing, 
            # we can use a dummy or the first customer found, or create one.
            # For simplicity, let's find the first customer or use current user as proxy
            customer = User.objects.filter(role='customer').first()
            if not customer:
                customer = request.user # Fallback
            
            # Create Order
            order = Order.objects.create(
                user=customer,
                created_by=request.user,
                total_amount=total_amount,
                paid_amount=advance_paid,
                status='confirmed',
                delivery_address=customer_address
            )
            
            # Create Items
            for item in items:
                # Try to find product by model number if possible
                model_parts = item.get('model', '').split(' - ')
                model_number = model_parts[0] if model_parts else ''
                product = Product.objects.filter(model_number=model_number).first()
                
                if product:
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=int(item.get('qty', 1)),
                        price=float(item.get('price', 0))
                    )
            
            # Create Payment
            Payment.objects.create(
                order=order,
                total_amount=total_amount,
                paid=advance_paid,
                pending=total_amount - advance_paid
            )
            
            # Create Invoice
            invoice = Invoice.objects.create(
                order=order,
                user=customer
            )
            
            return JsonResponse({'status': 'success', 'order_id': order.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    products = Product.objects.all().order_by('model_number')
    # print("Enter")
    # for i in products:
    #     print(i.name)
    return render(request, 'custom_admin/billing.html', {'products': products})
def invoices(request):
    # Fetch orders and optimize queries with select_related/prefetch_related
    # We exclude 'draft' to show only real bookings
    orders = Order.objects.exclude(status='draft').select_related('user').prefetch_related('items__product')
    
    orders_data = []
    
    for inv in orders:
        # Fetch orders (excluding drafts)
        orders = Order.objects.exclude(status='draft').select_related('user')
        
        orders_data = []
        for inv in orders:
            orders_data.append({
            "id": str(inv.id),
            "customerName": inv.user.full_name or inv.user.username,
            "customerMobile": inv.user.mobile or "No Mobile", # Added this line
            "date": inv.date.strftime('%d %b %Y'),
            "total": float(inv.total_amount),
            "advance": float(inv.paid_amount),
            "balance": float(inv.total_amount - inv.paid_amount),
            "userType": str(inv.user.role).lower(),
            "status": inv.get_status_display(),
            "items": [
                {
                    "lotNo": item.product.model_number,
                    "price": float(item.price),
                    "qty": item.quantity,
                    "total": float(item.price * item.quantity)
                } for item in inv.items.all()
            ]
        })  

    # Note the variable name 'orders_json' here
    return render(request, 'custom_admin/invoices.html', {'orders_json': orders_data})
    # return render(request, 'custom_admin/invoices.html', {
    #     'orders_json': orders_data
    # })
    # # Fetch all confirmed/pending orders
    # all_orders = Order.objects.all().order_by('-date')
    # return render(request,'custom_admin/invoices.html',{'orders': all_orders})

import json
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from .models import Order, OrderItem, Product

def reports(request):
    # १. Daily Bookings (Last 7 Days)
    last_7_days = timezone.now() - timedelta(days=6)
    daily_data = Order.objects.filter(date__gte=last_7_days)\
        .annotate(day=TruncDate('date'))\
        .values('day')\
        .annotate(count=Count('id'))\
        .order_by('day')
    
    booking_labels = [d['day'].strftime('%a') for d in daily_data]
    booking_counts = [d['count'] for d in daily_data]

    # २. Most Popular Models (Top 5)
    popular_models = OrderItem.objects.values('product__name')\
        .annotate(total_sold=Sum('quantity'))\
        .order_by('-total_sold')[:5]
    popular_labels = [p['product__name'] for p in popular_models]
    popular_counts = [p['total_sold'] for p in popular_models]

    # ३. Monthly Revenue
    monthly_data = Order.objects.annotate(month=TruncMonth('date'))\
        .values('month')\
        .annotate(total_revenue=Sum('total_amount'))\
        .order_by('month')
    revenue_labels = [m['month'].strftime('%b') for m in monthly_data]
    revenue_counts = [float(m['total_revenue']) for m in monthly_data]

    # ४. Financial Summary (Total, Paid, Pending)
    financials = Order.objects.aggregate(
        total=Sum('total_amount'),
        paid=Sum('paid_amount')
    )
    total_rev = financials['total'] or 0
    total_paid = financials['paid'] or 0
    total_pending = total_rev - total_paid

    # ५. Inventory Alerts (Low Stock < 10)
    low_stock_items = Product.objects.filter(stock__lt=10).order_by('stock')

    # ६. Role-wise Sales (Wholesaler vs Customer)
    role_data = Order.objects.values('user__role')\
        .annotate(total=Sum('total_amount'))
    role_labels = [r['user__role'].capitalize() for r in role_data]
    role_values = [float(r['total']) for r in role_data]

    context = {
        'booking_labels': json.dumps(booking_labels),
        'booking_counts': json.dumps(booking_counts),
        'popular_labels': json.dumps(popular_labels),
        'popular_counts': json.dumps(popular_counts),
        'revenue_labels': json.dumps(revenue_labels),
        'revenue_counts': json.dumps(revenue_counts),
        'role_labels': json.dumps(role_labels),
        'role_values': json.dumps(role_values),
        'total_rev': total_rev,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'low_stock_items': low_stock_items,
    }
    return render(request, 'custom_admin/reports.html', context)

def settings(request):
    user = request.user
    if request.method == "POST":
        action = request.POST.get('action')
        
        # update profile photo
        if action == "profile_photo":
            if request.FILES.get('profile_img'):
                user.profile_img = request.FILES.get('profile_img')
                user.save()
                messages.success(request, "Profile photo update successfully")
        
        # update personal info
        elif action == "profile_info":
            user.full_name = request.POST.get('full_name')
            user.email = request.POST.get('email')
            user.save()
            messages.success(request, "Personal details update successfully")
            
        # update business info
        elif action == "business_info":
            user.business_name = request.POST.get('business_name')
            user.proprietor_name = request.POST.get('proprietor_name')
            user.mobile = request.POST.get('mobile')
            user.mobile2 = request.POST.get('mobile2')
            user.mobile3 = request.POST.get('mobile3')
            user.address = request.POST.get('address')
            user.save()
            messages.success(request, "Business details update successfully")
            
        return redirect('admin_panel:settings') 

    return render(request, 'custom_admin/settings.html')







# custom orders list  
def manage_customer_orders(request):
    orders = Order.objects.filter(user__role='customer').order_by('-date')
    return render(request, 'custom_admin/manage_orders.html', {'orders': orders, 'title': 'Customer Orders'})

# wholesaler order list
def manage_wholesaler_orders(request):
    orders = Order.objects.filter(user__role='wholesaler').order_by('-date')
    return render(request, 'custom_admin/manage_orders.html', {'orders': orders, 'title': 'Wholesaler Orders'})

# update order status and qty
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == "POST":
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()
        
        # if change the qty update the (OrderItem)
        for item in order.items.all():
            qty_key = f"qty_{item.id}"
            if qty_key in request.POST:
                new_qty = int(request.POST.get(qty_key))
                
                #stock management: fetch the previous model stock update the new model stock
                product = item.product
                product.stock += item.quantity # reset
                product.stock -= new_qty # new minus 
                product.save()
                
                item.quantity = new_qty
                item.save()
        
        # recalculate total amount
        new_total = sum(item.get_total_item_price() for item in order.items.all())
        order.total_amount = new_total
        order.save()
        
        messages.success(request, f"Order #{order.id} updated successfully!")
        return redirect(request.META.get('HTTP_REFERER')) # redirect jithun aalot tithe

    return redirect('admin_panel:dashboard')

