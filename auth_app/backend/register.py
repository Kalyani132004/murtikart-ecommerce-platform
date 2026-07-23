from django.shortcuts import render, redirect
from django.contrib import messages
import string

#custom user model
from django.contrib.auth import get_user_model
User = get_user_model()

def register_view(request):
    if request.method == "POST":

        fullname = request.POST.get("fullname")
        email = request.POST.get("email")
        business_name = request.POST.get("business_name")
        role = request.POST.get("role")
        pass1 = request.POST.get("pass1")
        pass2 = request.POST.get("pass2")
        mobile = request.POST.get("mobile")

        #  Validation
        # check password length 
        if len(pass1) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
            return redirect('auth:register')

        #check the any special character exist or not 
        if not any(char in string.punctuation for char in pass1):
            messages.error(request, 'Password must have at least one special character')
            return redirect('auth:register')
            
        if pass1 != pass2:
            messages.error(request, "Passwords do not match")
            return redirect('auth:register')
        
        # if not request.POST.get("terms"):
        #     messages.error(request, "Accept terms first")
        #     return redirect('auth:register')

        if User.objects.filter(username=email).exists():
            messages.error(request, "User already exists")
            return redirect('auth:register')

        try:
            #  Name split
            name_parts = fullname.split()
            if len(name_parts)<2:
                messages.error(request, "Please enter full name")
                return redirect("auth:register")
            
            name = " ".join(name_parts)

            #  Role based user creation
            if role == "admin":
                user = User.objects.create_superuser(
                    username=email,
                    email=email,
                    password=pass1,
                    full_name=name,
                    role=role,
                    mobile=mobile,
                    business_name=business_name
                )

            elif role in ["customer", "wholesaler"]:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=pass1,
                    full_name=name,
                    role=role,
                    mobile=mobile,
                    business_name=business_name
                )

            else:
                messages.error(request, "Invalid role")
                return redirect('auth:register')

            messages.success(request, "Registration Successful ")
            return redirect('auth:login')

        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('auth:register')

    return render(request, 'auth/register.html')
