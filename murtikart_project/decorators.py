# (put wherever your shared utils live)
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please login to continue.")
                return redirect('auth:login')
            if request.user.role != role:
                messages.error(request, "You are not authorized to access this page.")
                return redirect('auth:login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# NEW — add this, for DRF @api_view endpoints only
from rest_framework.response import Response
from rest_framework import status
def api_role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return Response({'msg': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            if request.user.role != role:
                return Response({'msg': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
