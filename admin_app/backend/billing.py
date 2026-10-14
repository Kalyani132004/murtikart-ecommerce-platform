from admin_app.models import Product
from django.shortcuts import render
from murtikart_project.decorators import role_required
from django.contrib.auth.decorators import login_required

@role_required('admin')
@login_required
def billing(request):
    if request.method == 'POST':
        import json
        from django.http import JsonResponse
        from .models import Order, OrderItem, Payment, Invoice, User
        
        try:
            data = json.loads(request.body)
            customer_name = data.get('customer_name')
            customer_mobile = data.get('customer_mobile')
            customer_address = data.get('customer_address')
            items = data.get('items', [])
            total_amount = float(data.get('total_amount', 0))
            advance_paid = float(data.get('advance_paid', 0))
            
            # Find or create a guest customer user
            # Usually we'd want to link to an existing user, but for quick billing, 
            # we can use a dummy or the first customer found, or create one.
            # For simplicity, let's find the first customer or use current user as proxy
            customer = User.objects.filter(role='customer').first()
            if not customer:
                customer = request.user # Fallback
            
            # Create Order
            order = Order.objects.create(
                user=customer,
                created_by=request.user,
                total_amount=total_amount,
                paid_amount=advance_paid,
                status='confirmed',
                delivery_address=customer_address
            )
            
            # Create Items
            for item in items:
                # Try to find product by model number if possible
                model_parts = item.get('model', '').split(' - ')
                model_number = model_parts[0] if model_parts else ''
                product = Product.objects.filter(model_number=model_number).first()
                
                if product:
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=int(item.get('qty', 1)),
                        price=float(item.get('price', 0))
                    )
            
            # Create Payment
            Payment.objects.create(
                order=order,
                total_amount=total_amount,
                paid=advance_paid,
                pending=total_amount - advance_paid
            )
            
            # Create Invoice
            invoice = Invoice.objects.create(
                order=order,
                user=customer
            )
            
            return JsonResponse({'status': 'success', 'order_id': order.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    products = Product.objects.all().order_by('model_number')
    # print("Enter")
    # for i in products:
    #     print(i.name)
    return render(request, 'custom_admin/billing.html', {'products': products})