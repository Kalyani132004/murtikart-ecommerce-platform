from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .backend import login,logout,register
app_name = 'auth'

urlpatterns = [
    path('login/',    login.login_view,    name='login'),
    path('register/', register.register_view, name='register'),
    path('logout/',   logout.logout_view,   name='logout'),
    
    # Password Reset Links
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='auth/forgot_password/password_reset_form.html',
             success_url=reverse_lazy('auth:password_reset_done'),
             email_template_name='auth/forgot_password/password_reset_email.html'
         ), name='password_reset'),

    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='auth/forgot_password/password_reset_done.html'
         ), name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='auth/forgot_password/password_reset_confirm.html',
             success_url=reverse_lazy('auth:password_reset_complete') # redirect after all complete proccess
         ), name='password_reset_confirm'),

    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/forgot_password/password_reset_complete.html'
         ), name='password_reset_complete'),
]