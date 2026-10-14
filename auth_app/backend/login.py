from django.shortcuts import render, redirect
from admin_app.models import User
from django.contrib.auth import login,authenticate,logout
from django.contrib import messages

# def login_view(request):
#     if request.method == "POST":
#         email = request.POST.get("email")
#         password = request.POST.get("password")
#         role = request.POST.get("role") 
#         user = authenticate(request, username=email, password=password)
        
#         if user is not None:
#             if user.role != role:
#                 messages.error(request, "Invalid role! Please select your correct role.")
#                 return redirect("auth:login")
            
#             # if role match after login
#             login(request, user)
#             messages.success(request, f"Welcome back, {user.full_name}!")

#             # redirect with role
#             if user.role == 'admin':
#                 return redirect("admin_panel:dashboard")
#             elif user.role == 'customer':
#                 return redirect("customer:dashboard")
#             elif user.role == 'wholesaler':
#                 return redirect("wholesaler:dashboard")
#         else:
#             messages.error(request, "Invalid credentials")
#             return redirect('auth:login')
#     return render(request, 'auth/login.html')

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.role != role:
                messages.error(request, "Invalid role! Please select your correct role.")
                return redirect("auth:login")

            login(request, user)
            messages.success(request, f"Welcome back, {user.full_name}!")

            role_redirects = {
                'admin':      ("admin_panel:dashboard", "admin_sessionid"),
                'customer':   ("customer:dashboard", "customer_sessionid"),
                'wholesaler': ("wholesaler:dashboard", "wholesaler_sessionid"),
            }
            url_name, cookie_name = role_redirects[user.role]
            response = redirect(url_name)

            # bind this login to the role-specific cookie
            response.set_cookie(
                cookie_name,
                request.session.session_key,
                max_age=request.session.get_expiry_age(),
                httponly=True,
                samesite='Lax',
            )
            return response
        else:
            messages.error(request, "Invalid credentials")
            return redirect('auth:login')
    return render(request, 'auth/login.html')