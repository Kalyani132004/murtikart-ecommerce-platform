from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from murtikart_project.decorators import role_required

@role_required('wholesaler')
@login_required
def profile(request):
    user = request.user

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        business_name = request.POST.get('business_name', '').strip()
        address = request.POST.get('address', '').strip()
        profile_pic = request.FILES.get('profile_pic')

        if not full_name:
            messages.error(request, "Full name cannot be empty.")
            return redirect('wholesaler:profile')

        if mobile and (not mobile.isdigit() or len(mobile) != 10):
            messages.error(request, "Please enter a valid 10-digit mobile number.")
            return redirect('wholesaler:profile')

        if profile_pic:
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            max_size_mb = 5
            if profile_pic.content_type not in allowed_types:
                messages.error(request, "Only JPG, PNG, or WEBP images are allowed.")
                return redirect('wholesaler:profile')
            if profile_pic.size > max_size_mb * 1024 * 1024:
                messages.error(request, f"Image must be under {max_size_mb}MB.")
                return redirect('wholesaler:profile')
            user.profile_img = profile_pic

        user.full_name = full_name
        user.mobile = mobile
        user.business_name = business_name
        user.address = address
        user.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('wholesaler:profile')

    return render(request, 'wholesaler/profile.html', {'user': user})