
import json
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from admin_app.models import Order, Product,OrderItem

def reports(request):
    # daily bookings 7 days 
    last_7_days = timezone.now() - timedelta(days=6)
    daily_data = Order.objects.filter(date__gte=last_7_days)\
        .annotate(day=TruncDate('date'))\
        .values('day')\
        .annotate(count=Count('id'))\
        .order_by('day')
    
    booking_labels = [d['day'].strftime('%a') for d in daily_data]
    booking_counts = [d['count'] for d in daily_data]

    # most popular module top 5
    popular_models = OrderItem.objects.values('product__name')\
        .annotate(total_sold=Sum('quantity'))\
        .order_by('-total_sold')[:5]
    popular_labels = [p['product__name'] for p in popular_models]
    popular_counts = [p['total_sold'] for p in popular_models]

    # monthly revenue
    monthly_data = Order.objects.annotate(month=TruncMonth('date'))\
        .values('month')\
        .annotate(total_revenue=Sum('total_amount'))\
        .order_by('month')
    revenue_labels = [m['month'].strftime('%b') for m in monthly_data]
    revenue_counts = [float(m['total_revenue']) for m in monthly_data]

    # financial summury total paid, pending 
    financials = Order.objects.aggregate(
        total=Sum('total_amount'),
        paid=Sum('paid_amount')
    )
    total_rev = financials['total'] or 0
    total_paid = financials['paid'] or 0
    total_pending = total_rev - total_paid

    # inventry alerts (Low Stock < 10)
    low_stock_items = Product.objects.filter(stock__lt=10).order_by('stock')

    # role wise salers (Wholesaler vs Customer)
    role_data = Order.objects.values('user__role')\
        .annotate(total=Sum('total_amount'))
    role_labels = [r['user__role'].capitalize() for r in role_data]
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
