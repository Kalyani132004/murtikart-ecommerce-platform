from django.shortcuts import render
from admin_app.models import Product, Order, OrderItem, Payment, Invoice, User

from django.db.models import Sum, F
from django.contrib.auth.decorators import login_required
from murtikart_project.decorators import role_required

@role_required('admin')
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
