app_name = 'admin_panel'
from django.urls import path
from . import views
from .backend import (
    dashboard,models,bookings,customer,
    wholesalers,billing,invoices,reports,settings,manage_orders,discounts
        )
urlpatterns = [
    path('',           dashboard.dashboard,  name='dashboard'),
    path('models/',    models.models,     name='models'),
    path('models/add/',models.add_model,  name='add_model'),
    path('bookings/',  bookings.bookings_list,   name='bookings'),
    path('customers/', customer.customers,  name='customers'),
    path('wholesalers/',wholesalers.wholesalers,name='wholesalers'),
    path('wholesalers/orders/<int:order_id>/edit/', wholesalers.edit_wholesale_order, name='edit_wholesale_order'),
    #path('discounts/', views.discounts,  name='discounts'),
    path('billing/',   billing.billing,    name='billing'),
    path('invoices/',  invoices.invoices,   name='invoices'),
    path('reports/',   reports.reports,    name='reports'),
    path('settings/',  settings.settings,   name='settings'),
    
    #apis
    path('api/add/models/',models.save_models,name='get_models'),
    path('update-model/<str:pk>/', models.update_models, name='update_models'),
    path('delete-model/<str:pk>/', models.delete_model, name='delete_models'),
    
    path('api/visibility/check/',models.visibility_check,name='visibility_check'),
    
    #discount 
    path('discounts/', discounts.discount_list,  name='discount_list'),
    path('discounts/add/', discounts.add_discount, name='add_discount'),
    path('discounts/delete/<int:pk>/', discounts.delete_discount, name='delete_discount'),
    path('discounts/edit/<int:pk>/', discounts.edit_discount, name='edit_discount'),
    
    
    #order management
    path('manage-customer-orders/', manage_orders.manage_customer_orders, name='manage_customer_orders'),
    path('manage-wholesaler-orders/', manage_orders.manage_wholesaler_orders, name='manage_wholesaler_orders'),
    path('update-order-status/<int:order_id>/', manage_orders.update_order_status, name='update_order_status'),
]

# urlpatterns = [
#     path('',           views.dashboard,  name='dashboard'),
#     path('models/',    views.models,     name='models'),
#     path('models/add/',views.add_model,  name='add_model'),
#     path('bookings/',  views.bookings_list,   name='bookings'),
#     path('customers/', views.customers,  name='customers'),
#     path('wholesalers/',views.wholesalers,name='wholesalers'),
#     path('wholesalers/orders/<int:order_id>/edit/', views.edit_wholesale_order, name='edit_wholesale_order'),
#     #path('discounts/', views.discounts,  name='discounts'),
#     path('billing/',   views.billing,    name='billing'),
#     path('invoices/',  views.invoices,   name='invoices'),
#     path('reports/',   views.reports,    name='reports'),
#     path('settings/',  views.settings,   name='settings'),
    
#     #apis
#     path('api/add/models/',views.save_models,name='get_models'),
#     path('api/visibility/check/',views.visibility_check,name='visibility_check'),
    
#     #discount 
#     path('discounts/', views.discount_list,  name='discount_list'),
#     path('discounts/add/', views.add_discount, name='add_discount'),
#     path('discounts/delete/<int:pk>/', views.delete_discount, name='delete_discount'),
    
    
    
#     #order management
#     path('manage-customer-orders/', views.manage_customer_orders, name='manage_customer_orders'),
#     path('manage-wholesaler-orders/', views.manage_wholesaler_orders, name='manage_wholesaler_orders'),
#     path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
# ]
