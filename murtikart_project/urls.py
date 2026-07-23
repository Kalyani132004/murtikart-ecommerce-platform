"""
urls.py - URL Configuration for MurtiKart Django project
===============================================================
This file shows all the URL names expected by the templates.
Wire these to your views when you add the backend.

To use namespaces, each app must have app_name defined in its urls.py.
"""

from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib import admin
urlpatterns = [
    #admin
    path('django-admin/',admin.site.urls),
    
   #auth
    path('', include('auth_app.urls', namespace='auth')),
    
    #admin
    path('admin-portal/', include('admin_app.urls', namespace='admin_panel')),

    #customer
    path('customer/', include('customer_app.urls', namespace='customer')),

    #wholesaler
    path('wholesaler/', include('wholesaler_app.urls', namespace='wholesaler')),
    
]
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

