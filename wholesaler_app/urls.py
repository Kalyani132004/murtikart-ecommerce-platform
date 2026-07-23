app_name = 'wholesaler'
from django.urls import path
from . import views
from .backend import (
    dashboard,models,book,invoices,orders,
    offers, profile, 
)
urlpatterns = [
    path('',          dashboard.dashboard, name='dashboard'),
    path('models/',   models.models,    name='models'),
    #validation and confirm order code 
    path('book/',     book.book,      name='book'),
    path('invoices/', invoices.invoices,  name='invoices'),
    path('orders/',   orders.my_orders,    name='orders'),
    path('offers/',   offers.offers,    name='offers'),
    path('profile/',  profile.profile,   name='profile'), 
    #book validation api
    path('api/book/validation/', book.check_validation, name='booking_validation')
]

# urlpatterns = [
#     path('',          views.dashboard, name='dashboard'),
#     path('models/',   views.models,    name='models'),
#     path('book/',     views.book,      name='book'),
#     path('invoices/', views.invoices,  name='invoices'),
    
#     # path('billing/',  views.billing,   name='billing'),
#     path('orders/',   views.my_orders,    name='orders'),
#     #path('orders/',   views.orders,    name='orders'),
#     #path('orders/<int:order_id>/edit/', views.edit_order, name='edit_order'),
    
#     path('offers/',   views.offers,    name='offers'),
#     path('profile/',  views.profile,   name='profile'),
#     #path('invoices/', views.invoices,  name='invoices'),
    
#     path('api/book/validation/', views.check_validation, name='booking_validation')
# ]
