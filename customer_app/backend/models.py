from admin_app.models import *
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F,Q
import json
from django.shortcuts import render

@login_required
def models(request):
    #products = Product.objects.all()
    #fetch the model this model visibility is 'both' or 'customer'
    products = Product.objects.filter(
                Q(visibility='customer') | Q(visibility='both')
            )
    products_list = []
    for p in products:
        # model_type raw choices: 'decorated' or 'color'
        # Map to display values that match the template filters
        type_map = {'decorated': 'Decorated', 'color': 'Color'}
        products_list.append({
            'id': p.model_number,
            'name': p.name,
            'type': type_map.get(p.model_type, p.get_model_type_display()),
            'size': float(p.size) if p.size else 0,
            'price': float(p.price) if p.price else 0,
            'stock': p.stock if p.stock else 0,
            'image': p.image.url if p.image else '/static/assets/images/dagdusheth_gold.png'
        })
    # Use json.dumps for safe JSON serialization (avoids Django template escaping issues)
    products_json = json.dumps(products_list)
    return render(request, 'customer/models.html', {
        'products': products,
        'products_json': products_json
    })