from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from admin_app.models import *

@login_required
def bookings(request):
    # If 'orderitem_set' is giving an error, try fetching just the orders first
    # to see if the page loads. 
    orders = Order.objects.filter(user=request.user).order_by('-id')
    return render(request, 'customer/bookings.html', {'orders': orders})
