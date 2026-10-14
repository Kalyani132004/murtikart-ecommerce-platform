from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from murtikart_project.decorators import role_required


@role_required('customer')
@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        address = request.POST.get('address', '').strip()

        if not full_name:
            messages.error(request, "Full name cannot be empty.")
            return redirect('customer:profile')

        if mobile and (not mobile.isdigit() or len(mobile) != 10):
            messages.error(request, "Please enter a valid 10-digit mobile number.")
            return redirect('customer:profile')

        user.full_name = full_name

        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ""

        user.mobile = mobile
        user.address = address

        if 'profile_pic' in request.FILES:
            image = request.FILES['profile_pic']

            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            max_size_mb = 5
            if image.content_type not in allowed_types:
                messages.error(request, "Only JPG, PNG, or WEBP images are allowed.")
                return redirect('customer:profile')
            if image.size > max_size_mb * 1024 * 1024:
                messages.error(request, f"Image must be under {max_size_mb}MB.")
                return redirect('customer:profile')

            user.profile_img = image

        user.save()
        messages.success(request, "Details updated successfully")
        return redirect('customer:profile')

    return render(request, 'customer/profile.html', {'user': user})