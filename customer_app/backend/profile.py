from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        # update user model info 
        full_name = request.POST.get('full_name')
        user.full_name = full_name # full name field 
        
        # name split and save in django defoult field 
        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        user.mobile = request.POST.get('mobile')
        user.address = request.POST.get('address')
        
        #  manage profile image 
        if 'profile_pic' in request.FILES:
            user.profile_img = request.FILES['profile_pic']
            
        user.save()
        messages.success(request, "Update details successfully")
        return redirect('customer:profile')

    return render(request, 'customer/profile.html', {'user': user})
    