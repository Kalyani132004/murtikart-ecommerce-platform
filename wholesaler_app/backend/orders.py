from admin_app.models import *
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from murtikart_project.decorators import role_required

@role_required('wholesaler')
@login_required
def my_orders(request):
    #arrange orders in new to old orders
    orders = request.user.order_set.all().prefetch_related('items__product').order_by('-date')
    return render(request, 'wholesaler/my_orders.html', {'orders': orders})
