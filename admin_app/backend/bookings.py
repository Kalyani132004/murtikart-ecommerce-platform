from admin_app.models import Order
from django.shortcuts import render
from murtikart_project.decorators import role_required
from django.contrib.auth.decorators import login_required

@role_required('admin')
@login_required
def bookings_list(request):
    # Fetch all orders, newest first
    # prefetch_related('items__product') helps get product names without extra queries
    all_bookings = Order.objects.all().select_related('user').prefetch_related('items__product').order_by('-date')
    return render(request, 'custom_admin/bookings.html', {'bookings': all_bookings})