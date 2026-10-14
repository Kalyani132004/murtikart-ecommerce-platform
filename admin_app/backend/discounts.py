from admin_app.models import Discount
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from murtikart_project.decorators import role_required


@role_required('admin')
@login_required
def discount_list(request):
    discounts = Discount.objects.all().order_by('min_price')
    return render(request, 'custom_admin/discounts.html', {'discounts': discounts})


@role_required('admin')
@login_required
def add_discount(request):
    if request.method == "POST":
        tier_name = request.POST.get('tier_name')
        min_price = request.POST.get('min_price')
        max_price = request.POST.get('max_price')
        discount_percent = request.POST.get('discount_percent')

        try:
            min_price = float(min_price)
            max_price = float(max_price) if max_price else None
            discount_percent = float(discount_percent)
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid numeric values.")
            return redirect('admin_panel:discount_list')

        if not (0 < discount_percent <= 100):
            messages.error(request, "Discount percent must be between 1 and 100.")
            return redirect('admin_panel:discount_list')

        if max_price is not None and max_price <= min_price:
            messages.error(request, "Max price must be greater than min price.")
            return redirect('admin_panel:discount_list')

        Discount.objects.create(
            tier_name=tier_name,
            min_price=min_price,
            max_price=max_price,
            discount_percent=discount_percent
        )
        messages.success(request, "New discount tier added successfully!")
        return redirect('admin_panel:discount_list')

    return redirect('admin_panel:discount_list')


@role_required('admin')
@login_required
def delete_discount(request, pk):
    if request.method == "POST":
        discount = get_object_or_404(Discount, pk=pk)   # was Discount.objects.get() — see note below
        discount.delete()
        messages.warning(request, "Discount tier removed.")
        return redirect('admin_panel:discount_list')

    return redirect('admin_panel:discount_list')


@role_required('admin')
@login_required
def edit_discount(request, pk):
    discount_obj = get_object_or_404(Discount, pk=pk)

    if request.method == "POST":
        min_p = request.POST.get('min_price')
        max_p = request.POST.get('max_price')
        disc_per = request.POST.get('discount_percent')

        try:
            min_p = float(min_p)
            max_p = float(max_p) if max_p else None
            disc_per = float(disc_per)
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid numeric values.")
            return render(request, 'custom_admin/edit_discount.html', {'discount': discount_obj})

        if not (0 < disc_per <= 100):
            messages.error(request, "Discount percent must be between 1 and 100.")
            return render(request, 'custom_admin/edit_discount.html', {'discount': discount_obj})

        discount_obj.min_price = min_p
        discount_obj.max_price = max_p
        discount_obj.discount_percent = disc_per
        discount_obj.save()

        messages.success(request, "Discount tier updated successfully!")
        return redirect('admin_panel:discount_list')

    return render(request, 'custom_admin/edit_discount.html', {'discount': discount_obj})