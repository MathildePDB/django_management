from django.shortcuts import render
from django.views.generic.base import TemplateView

def index(request):
    return render(request, "home/index.html")

def profile(request):
    return render(request, "profile/profile.html")

class RegistrationCompleteView(TemplateView):
    template_name="django_registration/registration_complete.html"

class RegistrationClosedView(TemplateView):
    template_name="django_registration/registration_closed.html"

class ActivationCompleteView(TemplateView):
    template_name="django_registration/activation_complete.html"
