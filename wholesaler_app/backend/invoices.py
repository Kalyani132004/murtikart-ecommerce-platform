from decimal import Decimal
from django.db.models import Sum
from admin_app.models import Order, User
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from murtikart_project.decorators import role_required


@role_required('wholesaler')
@login_required
def invoices(request):
    orders = request.user.order_set.all().prefetch_related('items__product')

    grand_total = Decimal('0.00')
    total_discount_amt = Decimal('0.00')
    total_paid = orders.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0.00')

    for order in orders:
        subtotal = Decimal(str(order.get_cart_total))
        savings = Decimal(str(order.get_discount_savings))

        order.disc_amt = savings
        order.disc_per = round((savings / subtotal) * 100, 2) if subtotal > 0 else 0

        grand_total += subtotal
        total_discount_amt += savings

    final_payable = grand_total - total_discount_amt
    total_balance = final_payable - total_paid

    admin_shop = User.objects.filter(role='admin').first()
    admin_shop_address = admin_shop.address if admin_shop else ''

    context = {
        'orders': orders,
        'grand_total': grand_total,
        'total_discount': total_discount_amt,
        'final_payable': final_payable,
        'total_paid': total_paid,
        'total_balance': total_balance,
        'admin_shop_address': admin_shop_address,
    }
    return render(request, 'wholesaler/invoices.html', context)