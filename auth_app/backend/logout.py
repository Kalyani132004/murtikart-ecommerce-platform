from django.shortcuts import redirect
from django.contrib.auth import logout

# def  logout_view(request):
#     logout(request)
#     return redirect('auth:login')

def logout_view(request):
    cookie_name = getattr(request, 'session_cookie_name', 'sessionid')
    logout(request)
    response = redirect('auth:login')
    response.delete_cookie(cookie_name)
    return response