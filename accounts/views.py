from django.contrib.auth.views import LoginView

from .forms import CustomLoginForm


class CustomLoginView(LoginView):
    template_name = "login.html"
    authentication_form = CustomLoginForm
