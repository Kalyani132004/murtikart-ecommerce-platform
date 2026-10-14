from django.shortcuts import render
from admin_app.models import *
from django.contrib.auth.decorators import login_required
from murtikart_project.decorators import role_required

@role_required('customer')
@login_required
def offers(request):
    offers = Discount.objects.all().order_by('min_price')
    return render(request, 'customer/offers.html', {'offers': offers})
