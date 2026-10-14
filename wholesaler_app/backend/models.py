from admin_app.models import Product
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from murtikart_project.decorators import role_required


@role_required('wholesaler')
@login_required
def models(request):
    products = Product.objects.filter(
        Q(visibility='wholesaler') | Q(visibility='both')
    )
    products_list = []
    for p in products:
        type_map = {'decorated': 'Decorated', 'color': 'Color'}
        products_list.append({
            'id': p.model_number,
            'name': p.name,
            'type': type_map.get(p.model_type, p.get_model_type_display()),
            'size': float(p.size) if p.size else 0,
            'price': float(p.price) if p.price else 0,
            'stock': p.stock if p.stock else 0,
            'image': p.image.url if p.image else '/media/no-image-placeholder.png'
        })
    return render(request, 'wholesaler/models.html', {
        'products': products,
        'products_list': products_list,
    })