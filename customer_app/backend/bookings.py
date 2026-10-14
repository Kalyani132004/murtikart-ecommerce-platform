from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from admin_app.models import Order
from murtikart_project.decorators import role_required


@role_required('customer')
@login_required
def bookings(request):
    orders = Order.objects.filter(user=request.user) \
        .select_related('payment') \
        .prefetch_related('items__product') \
        .order_by('-id')

    return render(request, 'customer/bookings.html', {'orders': orders})