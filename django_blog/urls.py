"""
URL configuration for django_blog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django_blog import views
from django.contrib.auth.views import *
from django_registration.backends.activation.views import ActivationView, RegistrationView
from . import views as v

urlpatterns = [
    path('', views.index, name="index"),
    path('business/', include("business.urls")),
    path('admin/', admin.site.urls),
    path('profile/', views.profile, name="profile"),
    path('accounts/activate/<str:activation_key>/', ActivationView.as_view(), 
         name="django_registration_activate"),
    path('accounts/activate/complete/', v.ActivationCompleteView.as_view(), name="django_registration_activation_complete"),
    path('accounts/login/', LoginView.as_view(
            template_name="django_registration/login.html"
        ), name="login"),
    path('accounts/logout/', LogoutView.as_view(), name="logout"),
    path('accounts/password_change/', PasswordChangeView.as_view(
            template_name='django_registration/password_change_form.html',
            success_url='/accounts/password_change/done/'
        ), name='password_change'),
    path('accounts/password_change/done/', PasswordChangeDoneView.as_view(
            template_name='django_registration/password_change_done.html'
        ), name='password_change_done'),
    path('accounts/password_reset/', PasswordResetView.as_view(
        template_name='django_registration/password_reset_form.html'
    ), name="password_reset"),
    path('accounts/password_reset/done/', PasswordResetDoneView.as_view(
        template_name='django_registration/password_reset.html'
    ), name="password_reset_done"),
    path('accounts/register/', RegistrationView.as_view(
        template_name="django_registration/registration_form.html",
    ), name="django_registration_register"),
    path('accounts/register/closed/', v.RegistrationClosedView.as_view(), name="django_registration_disallowed"),
    path('accounts/register/complete/', v.RegistrationCompleteView.as_view(), name="django_registration_complete"),
    path('accounts/reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='django_registration/password_reset_new_form.html'
    ), name="password_reset_confirm"),
    path('accounts/reset/done/', PasswordResetCompleteView.as_view(
        template_name="django_registration/password_reset_done.html",
    ), name="password_reset_complete"),
    # path('accounts/', include('django_registration.backends.activation.urls')),
    path('__debug__/', include("debug_toolbar.urls")),
]
