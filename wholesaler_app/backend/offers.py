from admin_app.models import *
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def offers(request):
    offers = Discount.objects.all().order_by('min_price')
    return render(request, 'wholesaler/offers.html', {'offers': offers})
 