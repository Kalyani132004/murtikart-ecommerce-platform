from admin_app.models import User
from django.shortcuts import render

def customers(request):
    # Fetch all users with the role 'customer'
    customer_list = User.objects.filter(role='customer').order_by('-date_joined')
    return render(request, 'custom_admin/customers.html', {'customers': customer_list})
