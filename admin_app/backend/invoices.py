from admin_app.models import Order
from django.shortcuts import render
from murtikart_project.decorators import role_required
from django.contrib.auth.decorators import login_required

@role_required('admin')
@login_required
def invoices(request):
    orders = Order.objects.exclude(status='draft') \
        .select_related('user') \
        .prefetch_related('items__product')

    orders_data = []
    for inv in orders:
        orders_data.append({
            "id": str(inv.id),
            "customerName": inv.user.full_name or inv.user.username,
            "customerMobile": inv.user.mobile or "No Mobile",
            "date": inv.date.strftime('%d %b %Y'),
            "total": float(inv.total_amount),
            "advance": float(inv.paid_amount),
            "balance": float(inv.total_amount - inv.paid_amount),
            "userType": str(inv.user.role).lower(),
            "status": inv.get_status_display(),
            "items": [
                {
                    "lotNo": item.product.model_number,
                    "price": float(item.price),
                    "qty": item.quantity,
                    "total": float(item.price * item.quantity)
                } for item in inv.items.all()
            ]
        })

    return render(request, 'custom_admin/invoices.html', {'orders_json': orders_data})