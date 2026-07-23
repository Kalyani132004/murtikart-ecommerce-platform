from admin_app.models import Order, User, Payment,Product,OrderItem
from django.shortcuts import redirect,render, get_object_or_404
import json
from django.http import JsonResponse

def wholesalers(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        action = request.POST.get('action')
        try:
            order = Order.objects.get(id=order_id)
            if action == 'confirm':
                order.status = 'confirmed'
                order.save()
            elif action == 'cancel':
                order.status = 'cancelled'
                order.save()
            elif action == 'deliver':
                order.status = 'delivered'
                order.save()
        except Order.DoesNotExist:
            pass
        return redirect('admin_panel:wholesalers')

    # Show all wholesale orders (except drafts)
    wholesale_orders = Order.objects.filter(
        user__role='wholesaler'
    ).exclude(status='draft').select_related('user').prefetch_related('items__product').order_by('-date')
    wholesaler_users = User.objects.filter(role='wholesaler')
    return render(request, 'custom_admin/wholesalers.html', {
        'wholesale_orders': wholesale_orders,
        'wholesaler_users': wholesaler_users,
    })

def edit_wholesale_order(request, order_id):
    """Admin edits / updates a wholesale order."""
    order = get_object_or_404(Order, id=order_id, user__role='wholesaler')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            note = data.get('note', order.delivery_address or '')
            status = data.get('status', order.status)

            if not items:
                return JsonResponse({'status': 'error', 'message': 'No items selected.'}, status=400)

            # Replace all items
            order.items.all().delete()
            total = 0
            for item in items:
                product = Product.objects.filter(model_number=item.get('model_number')).first()
                if product:
                    qty = int(item.get('qty', 1))
                    price = float(product.price)
                    OrderItem.objects.create(order=order, product=product, quantity=qty, price=price)
                    total += price * qty

            order.total_amount = total
            order.delivery_address = note
            order.status = status
            order.save()

            payment = Payment.objects.filter(order=order).first()
            if payment:
                payment.total_amount = total
                payment.pending = max(0, total - float(payment.paid))
                payment.save()

            return JsonResponse({'status': 'success', 'order_id': order.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # GET - load edit page
    products = Product.objects.all().order_by('model_number')
    products_json = json.dumps([{
        'model_number': p.model_number,
        'name': p.name,
        'price': float(p.price) if p.price else 0,
        'stock': p.stock if p.stock else 0,
        'image': p.image.url if p.image else '/static/assets/images/dagdusheth_gold.png'
    } for p in products])

    existing_items = {}
    for item in order.items.all():
        existing_items[item.product.model_number] = item.quantity

    return render(request, 'custom_admin/edit_wholesale_order.html', {
        'order': order,
        'products': products,
        'products_json': products_json,
        'existing_items_json': json.dumps(existing_items),
    })