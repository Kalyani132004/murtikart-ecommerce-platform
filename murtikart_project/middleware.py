#  (adjust app path if needed)
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.utils.http import http_date
from importlib import import_module
import time

ROLE_COOKIE_MAP = {
    '/admin-portal/': 'admin_sessionid',   # ✅ match actual URL
    '/wholesaler/':   'wholesaler_sessionid',
    '/customer/':     'customer_sessionid',
}
# 👆 update these prefixes to match your actual dashboard URLs

class RoleSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        engine = import_module(settings.SESSION_ENGINE)
        cookie_name = settings.SESSION_COOKIE_NAME  # default 'sessionid' (used for /auth/)

        for prefix, name in ROLE_COOKIE_MAP.items():
            if request.path.startswith(prefix):
                cookie_name = name
                break

        request.session_cookie_name = cookie_name
        session_key = request.COOKIES.get(cookie_name)
        request.session = engine.SessionStore(session_key)

    def process_response(self, request, response):
        try:
            modified = request.session.modified
        except AttributeError:
            return response

        if modified or settings.SESSION_SAVE_EVERY_REQUEST:
            max_age = request.session.get_expiry_age()
            expires = http_date(time.time() + max_age)
            request.session.save()
            response.set_cookie(
                request.session_cookie_name,
                request.session.session_key,
                max_age=max_age,
                expires=expires,
                httponly=settings.SESSION_COOKIE_HTTPONLY,
                samesite=settings.SESSION_COOKIE_SAMESITE,
            )
        return response
    

from django.shortcuts import redirect
from django.contrib import messages

class RoleAccessMiddleware:
    ROLE_PREFIX_MAP = {
        '/admin-portal/': 'admin',
        '/wholesaler/':   'wholesaler',
        '/customer/':     'customer',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for prefix, role in self.ROLE_PREFIX_MAP.items():
            if request.path.startswith(prefix):
                if not request.user.is_authenticated:
                    messages.error(request, "Please login to continue.")
                    return redirect('auth:login')
                if request.user.role != role:
                    messages.error(request, "You are not authorized to access this page.")
                    return redirect('auth:login')
                break
        return self.get_response(request)
    
    