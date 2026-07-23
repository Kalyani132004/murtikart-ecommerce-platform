from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from admin_app.models import User

@login_required
def invoices(request):
    # with the help of prefetch_related easily gets the product price 
    orders = request.user.order_set.all().prefetch_related('items__product').order_by('-id')
    
    for order in orders:
        # fetch the actual price (4200 * 3 = 12600)
        # sometimes item.price have the discount price so i used the item.product.price 
        gross = sum(item.product.price * item.quantity for item in order.items.all())
        
        # join this variables on Order object
        order.calculated_gross = Decimal(str(gross))
        order.calculated_disc = order.calculated_gross - Decimal(str(order.total_amount))
        
        # if discount is less than 0 so set the 0
        if order.calculated_disc < 0:
            order.calculated_disc = Decimal('0.00')
            
    admin_shop_address = User.objects.get(email='kp8176778@gmail.com')
    return render(request, 'customer/invoices.html', {'orders': orders,'admin_shop_address':admin_shop_address.address})