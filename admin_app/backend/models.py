from django.shortcuts import render
from admin_app.models import Product
from django.core.serializers import serialize

from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes

from rest_framework.response import Response

from admin_app.serializers import ProductSerializer

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from murtikart_project.decorators import role_required
from murtikart_project.decorators import role_required, api_role_required   # 👈 add api_role_required
from rest_framework.permissions import IsAuthenticated


@role_required('admin')
@login_required
def models(request):
    all_models = Product.objects.all()
    all_models_json = serialize('json', all_models)

    return render(request, 'custom_admin/models.html', {
        'all_models': all_models,
        'all_models_json': all_models_json
})
    
@role_required('admin')
def add_model(request):
    return render(request,'custom_admin/add-model.html')
# save the new model 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@api_role_required('admin')
def save_models(request):
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"msg": "Model saved successfully"})
    return Response(serializer.errors)

@role_required('admin')
@login_required
def update_models(request, pk):
    # which model update want to update this model pk take this 
    product = get_object_or_404(Product, model_number=pk)

    if request.method == "POST":
        # collect the form data 
        product.model_number = request.POST.get('model_number')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        # update the image 
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        
        product.save()
        messages.success(request, f"Model {product.model_number} updated successfully!")
        return redirect('admin_panel:models') # model list page name 
    
    return render(request, 'custom_admin/update_model.html', {'product': product})

@role_required('admin')
@login_required
def delete_model(request, pk):
    # 'pk' will contain the string 'MK-110'. 
    # We will find that data according to the field 'model_number'.
    product = get_object_or_404(Product, model_number=pk)
    
    if request.method == "POST":
        deleted_name = product.model_number
        product.delete()
        messages.success(request, f"Model {deleted_name} deleted sucessfully.")
        return redirect('admin_panel:models')

    # If someone tries directly from the URL, send it back to the list
    return redirect('admin_panel:models')

# set the vissibility status
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@api_role_required('admin')
def visibility_check(request):
    try:
        data = request.data
        role = data.get('role')
        model_id = data.get('modelid')
        is_checked = data.get('is_checked')

        product = Product.objects.get(model_number=model_id)
        current = product.visibility
        new_visibility = current

        if role == 'customer':
            if is_checked:
                new_visibility = 'both' if current == 'wholesaler' else 'customer'
            else:
                new_visibility = 'wholesaler' if current == 'both' else 'none'

        elif role == 'wholesaler':
            if is_checked:
                new_visibility = 'both' if current == 'customer' else 'wholesaler'
            else:
                new_visibility = 'customer' if current == 'both' else 'none'

        product.visibility = new_visibility
        product.save()

        return Response({"msg": f"Updated to {new_visibility}"}, status=200)

    except Product.DoesNotExist:
        return Response({"msg": "Product not found"}, status=404)
    except Exception as e:
        return Response({"msg": str(e)}, status=500)