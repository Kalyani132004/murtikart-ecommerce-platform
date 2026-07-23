from admin_app.models import Discount
from django.contrib import messages

from django.shortcuts import render,redirect, get_object_or_404
def discount_list(request):
    discounts = Discount.objects.all().order_by('min_price')
    return render(request, 'custom_admin/discounts.html', {'discounts': discounts})

def add_discount(request):
    if request.method == "POST":
        tier_name = request.POST.get('tier_name')
        min_price = request.POST.get('min_price')
        max_price = request.POST.get('max_price')
        discount_percent = request.POST.get('discount_percent')

        Discount.objects.create(
            tier_name=tier_name,
            min_price=min_price,
            max_price=max_price,
            discount_percent=discount_percent
        )
        messages.success(request, "New discount tier added successfully!")
        return redirect('admin_panel:discount_list')

def delete_discount(request, pk):
    if request.method == "POST":
        discount = Discount.objects.get(pk=pk)
        discount.delete()
        messages.warning(request, "Discount tier removed.")
        
        return redirect('admin_panel:discount_list')
    
def edit_discount(request, pk):
    discount_obj = get_object_or_404(Discount, pk=pk)
    
    if request.method == "POST":
        #get the new form data  
        min_p = request.POST.get('min_price')
        max_p = request.POST.get('max_price')
        disc_per = request.POST.get('discount_percent')
        
        # insert the new data
        discount_obj.min_price = min_p
        discount_obj.max_price = max_p if max_p else None
        discount_obj.discount_percent = disc_per
        
        # saved in the DB
        discount_obj.save()
        
        # redirect main discount page 
        return redirect('admin_panel:discount_list')
        
    return render(request, 'custom_admin/edit_discount.html', {'discount': discount_obj})
    