from admin_app.models import Order
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

# custom orders list  
def manage_customer_orders(request):
    orders = Order.objects.filter(user__role='customer').order_by('-date')
    return render(request, 'custom_admin/manage_orders.html', {'orders': orders, 'title': 'Customer Orders'})

# wholesaler order list
def manage_wholesaler_orders(request):
    orders = Order.objects.filter(user__role='wholesaler').order_by('-date')
    return render(request, 'custom_admin/manage_orders.html', {'orders': orders, 'title': 'Wholesaler Orders'})

def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == "POST":
        old_status = order.status # old status stored 
        new_status = request.POST.get('status')
        
        order.status = new_status
        order.save()
        
        # Increase stock only if the new status is 'cancelled' and the old status was not 'cancelled'
        if new_status == 'cancelled' and old_status != 'cancelled':
            for item in order.items.all():
                product = item.product
                product.stock += item.quantity # स्टॉक परत वाढवला
                product.save()
                
        # 2. If Status is not Cancel and you are only updating Qty (old logic)
        elif new_status != 'cancelled':
            for item in order.items.all():
                qty_key = f"qty_{item.id}"
                if qty_key in request.POST:
                    new_qty = int(request.POST.get(qty_key))
                    
                    if new_qty != item.quantity:
                        product = item.product
                        #Reset the old stock and minus the new one
                        product.stock += item.quantity 
                        product.stock -= new_qty 
                        product.save()
                        
                        item.quantity = new_qty
                        item.save()

        # 3. Recalculate the total amount
        new_total = sum(item.price * item.quantity for item in order.items.all())
        order.total_amount = new_total
        order.save()
        
        messages.success(request, f"Order #{order.id} updated successfully!")
        return redirect(request.META.get('HTTP_REFERER'))

    return redirect('admin_panel:dashboard')