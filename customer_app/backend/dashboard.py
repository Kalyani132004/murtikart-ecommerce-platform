from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from admin_app.models import Product, Order
from django.db.models import Sum, F

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
