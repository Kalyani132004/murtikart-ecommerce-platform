from django.shortcuts import render
from admin_app.models import Product
from django.core.serializers import serialize

from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view

from rest_framework.response import Response

from admin_app.serializers import ProductSerializer

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

@login_required
def models(request):
    all_models = Product.objects.all()
    all_models_json = serialize('json', all_models)

    return render(request, 'custom_admin/models.html', {
        'all_models': all_models,
        'all_models_json': all_models_json
})
def add_model(request):
    return render(request,'custom_admin/add-model.html')
# save the new model 
@api_view(['POST'])
def save_models(request):
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"msg": "Model saved successfully"})
    return Response(serializer.errors)

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
def visibility_check(request):
    try:
        data = request.data
        role = data.get('role')          # 'customer' or 'wholesaler'
        model_id = data.get('modelid')
        is_checked = data.get('is_checked') # True or False

        product = Product.objects.get(model_number=model_id)
        current = product.visibility
        new_visibility = current

        if role == 'customer':
            if is_checked:
                # If turning customer ON, check if wholesaler is already ON
                new_visibility = 'both' if current == 'wholesaler' else 'customer'
            else:
                # If turning customer OFF, check if it was 'both'
                new_visibility = 'wholesaler' if current == 'both' else 'none'

        elif role == 'wholesaler':
            if is_checked:
                # If turning wholesaler ON, check if customer is already ON
                new_visibility = 'both' if current == 'customer' else 'wholesaler'
            else:
                # If turning wholesaler OFF, check if it was 'both'
                new_visibility = 'customer' if current == 'both' else 'none'

        # Update the database
        product.visibility = new_visibility
        product.save()

        return Response({"msg": f"Updated to {new_visibility}"}, status=200)

    except Product.DoesNotExist:
        return Response({"msg": "Product not found"}, status=404)
    except Exception as e:
        return Response({"msg": str(e)}, status=500)