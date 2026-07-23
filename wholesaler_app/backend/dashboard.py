from admin_app.models import *
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

@login_required
def dashboard(request):
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
