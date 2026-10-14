# customer/backend/invoices.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from admin_app.models import User
from murtikart_project.decorators import role_required


@role_required('customer')
@login_required
def invoices(request):
    orders = request.user.order_set.all() \
        .prefetch_related('items__product') \
        .order_by('-id')

    admin_shop = User.objects.filter(role='admin').first()
    admin_shop_address = admin_shop.address if admin_shop else ''

    return render(request, 'customer/invoices.html', {
        'orders': orders,
        'admin_shop_address': admin_shop_address,
    })