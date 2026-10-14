
import json
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from admin_app.models import Order, Product,OrderItem
from murtikart_project.decorators import role_required
from django.contrib.auth.decorators import login_required

@role_required('admin')
@login_required
def reports(request):
    # base queryset — exclude non-real orders (draft + unpaid/abandoned)
    valid_orders = Order.objects.exclude(status__in=['draft', 'pending_payment'])

    # daily bookings 7 days
    last_7_days = timezone.now() - timedelta(days=6)
    daily_data = valid_orders.filter(date__gte=last_7_days)\
        .annotate(day=TruncDate('date'))\
        .values('day')\
        .annotate(count=Count('id'))\
        .order_by('day')

    booking_labels = [d['day'].strftime('%a') for d in daily_data]
    booking_counts = [d['count'] for d in daily_data]

    # most popular model top 5 — only count items from valid orders
    popular_models = OrderItem.objects.filter(order__in=valid_orders)\
        .values('product__name')\
        .annotate(total_sold=Sum('quantity'))\
        .order_by('-total_sold')[:5]
    popular_labels = [p['product__name'] for p in popular_models]
    popular_counts = [p['total_sold'] for p in popular_models]

    # monthly revenue
    monthly_data = valid_orders.annotate(month=TruncMonth('date'))\
        .values('month')\
        .annotate(total_revenue=Sum('total_amount'))\
        .order_by('month')
    revenue_labels = [m['month'].strftime('%b') for m in monthly_data]
    revenue_counts = [float(m['total_revenue']) for m in monthly_data]

    # financial summary
    financials = valid_orders.aggregate(
        total=Sum('total_amount'),
        paid=Sum('paid_amount')
    )
    total_rev = financials['total'] or 0
    total_paid = financials['paid'] or 0
    total_pending = total_rev - total_paid

    # inventory alerts — unaffected, stock isn't order-status dependent
    low_stock_items = Product.objects.filter(stock__lt=10).order_by('stock')

    # role-wise sales
    role_data = valid_orders.values('user__role')\
        .annotate(total=Sum('total_amount'))
    role_labels = [r['user__role'].capitalize() if r['user__role'] else 'Unknown' for r in role_data]
    role_values = [float(r['total']) for r in role_data]

    context = {
        'booking_labels': json.dumps(booking_labels),
        'booking_counts': json.dumps(booking_counts),
        'popular_labels': json.dumps(popular_labels),
        'popular_counts': json.dumps(popular_counts),
        'revenue_labels': json.dumps(revenue_labels),
        'revenue_counts': json.dumps(revenue_counts),
        'role_labels': json.dumps(role_labels),
        'role_values': json.dumps(role_values),
        'total_rev': total_rev,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'low_stock_items': low_stock_items,
    }
    return render(request, 'custom_admin/reports.html', context)