from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from murtikart_project.decorators import role_required
from django.contrib.auth.decorators import login_required
from admin_app.models import User


@role_required('admin')
@login_required
def settings(request):
    user = request.user
    if request.method == "POST":
        action = request.POST.get('action')

        if action == "profile_photo":
            if request.FILES.get('profile_img'):
                image = request.FILES.get('profile_img')

                # basic file validation
                allowed_types = ['image/jpeg', 'image/png', 'image/webp']
                max_size_mb = 5
                if image.content_type not in allowed_types:
                    messages.error(request, "Only JPG, PNG, or WEBP images are allowed.")
                    return redirect('admin_panel:settings')
                if image.size > max_size_mb * 1024 * 1024:
                    messages.error(request, f"Image must be under {max_size_mb}MB.")
                    return redirect('admin_panel:settings')

                user.profile_img = image
                user.save()
                messages.success(request, "Profile photo updated successfully")
            else:
                messages.error(request, "Please select an image to upload.")

        elif action == "profile_info":
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()

            if not full_name:
                messages.error(request, "Full name cannot be empty.")
                return redirect('admin_panel:settings')

            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, "Please enter a valid email address.")
                return redirect('admin_panel:settings')

            # check email isn't already used by another account
            if User.objects.exclude(pk=user.pk).filter(email=email).exists():
                messages.error(request, "This email is already in use by another account.")
                return redirect('admin_panel:settings')

            user.full_name = full_name
            user.email = email
            user.username = email   # keep username in sync since login uses email as username
            user.save()
            messages.success(request, "Personal details updated successfully")

        elif action == "business_info":
            user.business_name = request.POST.get('business_name', '').strip()
            user.proprietor_name = request.POST.get('proprietor_name', '').strip()
            user.mobile = request.POST.get('mobile', '').strip()
            user.mobile2 = request.POST.get('mobile2', '').strip()
            user.mobile3 = request.POST.get('mobile3', '').strip()
            user.address = request.POST.get('address', '').strip()
            user.save()
            messages.success(request, "Business details updated successfully")

        else:
            messages.error(request, "Unknown action.")

        return redirect('admin_panel:settings')

    return render(request, 'custom_admin/settings.html')

