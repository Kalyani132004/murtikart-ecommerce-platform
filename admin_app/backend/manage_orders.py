# admin_panel/backend/manage_orders.py
from admin_app.models import Order
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from murtikart_project.decorators import role_required
from django.contrib.auth.decorators import login_required
from django.db import transaction

# custom orders list
@role_required('admin')
@login_required
def manage_customer_orders(request):
    orders = Order.objects.filter(user__role='customer').order_by('-date')
    return render(request, 'custom_admin/manage_orders.html', {'orders': orders, 'title': 'Customer Orders'})

# wholesaler order list
@role_required('admin')
@login_required
def manage_wholesaler_orders(request):
    orders = Order.objects.filter(user__role='wholesaler').order_by('-date')
    return render(request, 'custom_admin/manage_orders.html', {'orders': orders, 'title': 'Wholesaler Orders'})


@role_required('admin')
@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Where to send the admin back to, based on which order type this is
    def redirect_back():
        if order.user.role == 'wholesaler':
            return redirect('admin_panel:manage_wholesaler_orders')
        return redirect('admin_panel:manage_customer_orders')

    if request.method == "POST":
        old_status = order.status
        new_status = request.POST.get('status')

        # --- Fix #2: validate status against real choices ---
        valid_statuses = dict(Order.STATUS_CHOICES).keys()  # 👈 adjust attr name to match your model
        if new_status not in valid_statuses:
            messages.error(request, "Invalid status value.")
            return redirect_back()

        with transaction.atomic():
            order.status = new_status

            # Increase stock only if newly cancelled
            if new_status == 'cancelled' and old_status != 'cancelled':
                for item in order.items.select_related('product'):
                    product = item.product
                    product.stock += item.quantity
                    product.save()

            # Quantity updates (only when not cancelling)
            elif new_status != 'cancelled':
                for item in order.items.select_related('product'):
                    qty_key = f"qty_{item.id}"
                    if qty_key not in request.POST:
                        continue

                    # --- Fix #3a: safe int parsing ---
                    try:
                        new_qty = int(request.POST.get(qty_key))
                    except (ValueError, TypeError):
                        messages.error(request, f"Invalid quantity for item #{item.id}.")
                        continue

                    if new_qty < 1:
                        messages.error(request, f"Quantity must be at least 1 for item #{item.id}.")
                        continue

                    if new_qty != item.quantity:
                        product = item.product
                        available_after_revert = product.stock + item.quantity

                        # --- Fix #3b: prevent negative stock ---
                        if new_qty > available_after_revert:
                            messages.error(
                                request,
                                f"Not enough stock for {product.name}. Only {available_after_revert} available."
                            )
                            continue

                        product.stock = available_after_revert - new_qty
                        product.save()

                        item.quantity = new_qty
                        item.save()

            # Recalculate total
            new_total = sum(item.price * item.quantity for item in order.items.all())
            order.total_amount = new_total
            order.save()

        messages.success(request, f"Order #{order.id} updated successfully!")
        # --- Fix #1: no more HTTP_REFERER redirect ---
        return redirect_back()

    return redirect('admin_panel:dashboard')