from admin_app.models import *
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
    
@login_required
def profile(request):
    user = request.user
    
    if request.method == 'POST':
        # get data 
        full_name = request.POST.get('full_name')
        mobile = request.POST.get('mobile')
        business_name = request.POST.get('business_name')
        address = request.POST.get('address')
        profile_pic = request.FILES.get('profile_pic') 

        # update details in user model
        user.full_name = full_name
        user.mobile = mobile
        user.address = address
        
        # if model have bussiness_name field used this 
        if hasattr(user, 'business_name'):
            user.business_name = business_name
            
        # if update profile use this 
        if profile_pic:
            user.profile_img = profile_pic 

        user.save()
        messages.success(request, "Profile Updated Successfully!")
        return redirect('wholesaler:profile') #profile url

    return render(request, 'wholesaler/profile.html')