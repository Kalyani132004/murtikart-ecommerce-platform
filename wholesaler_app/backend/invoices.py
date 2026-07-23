from django.db.models import Sum, Q
from admin_app.models import *
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
 
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
    
    admin_shop_address = User.objects.get(email='kp8176778@gmail.com')
    
    context = {
        'orders': orders,
        'grand_total': grand_total,
        'total_discount': total_discount_amt,
        'final_payable': final_payable,
        'total_paid': total_paid,
        'total_balance': total_balance,
        'admin_shop_address': admin_shop_address.address
    }
    return render(request, 'wholesaler/invoices.html', context)
