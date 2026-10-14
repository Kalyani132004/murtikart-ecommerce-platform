from admin_app.models import User
from django.shortcuts import render
from murtikart_project.decorators import role_required
from django.contrib.auth.decorators import login_required

@role_required('admin')
@login_required
def customers(request):
    # Fetch all users with the role 'customer'
    customer_list = User.objects.filter(role='customer').order_by('-date_joined')
    return render(request, 'custom_admin/customers.html', {'customers': customer_list})
