from django.shortcuts import render,redirect
from django.contrib import messages

def settings(request):
    user = request.user
    if request.method == "POST":
        action = request.POST.get('action')
        
        # update profile photo
        if action == "profile_photo":
            if request.FILES.get('profile_img'):
                user.profile_img = request.FILES.get('profile_img')
                user.save()
                messages.success(request, "Profile photo update successfully")
        
        # update personal info
        elif action == "profile_info":
            user.full_name = request.POST.get('full_name')
            user.email = request.POST.get('email')
            user.save()
            messages.success(request, "Personal details update successfully")
            
        # update business info
        elif action == "business_info":
            user.business_name = request.POST.get('business_name')
            user.proprietor_name = request.POST.get('proprietor_name')
            user.mobile = request.POST.get('mobile')
            user.mobile2 = request.POST.get('mobile2')
            user.mobile3 = request.POST.get('mobile3')
            user.address = request.POST.get('address')
            user.save()
            messages.success(request, "Business details update successfully")
            
        return redirect('admin_panel:settings') 

    return render(request, 'custom_admin/settings.html')
