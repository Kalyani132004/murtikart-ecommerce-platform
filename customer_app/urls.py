from django.urls import path
from .backend import dashboard, models, book, bookings, invoices, profile, offers

app_name = 'customer'

urlpatterns = [
    path('', dashboard.dashboard, name='dashboard'),
    path('models/', models.models, name='models'),
    path('book/', book.book, name='book'),
    path('bookings/', bookings.bookings, name='bookings'),
    path('invoices/', invoices.invoices, name='invoices'),
    path('profile/', profile.profile, name='profile'),
    path('offers/', offers.offers, name='offers'),

    path('api/book/validation/', book.check_validation, name='booking_validation'),
    path('book/verify-payment/', book.verify_payment, name='verify_payment'),
]

# urlpatterns = [
#     path('',          views.dashboard, name='dashboard'),
#     path('models/',   views.models,    name='models'),
#     path('book/',     views.book,      name='book'),
#     path('bookings/', views.bookings,  name='bookings'),
#     path('invoices/', views.invoices,  name='invoices'),
#     path('profile/',  views.profile,   name='profile'),
#     path('offers/',  views.offers,   name='offers'),

#     #api get model details
#     path('api/book/validation/', views.check_validation, name='booking_validation')

# ]
