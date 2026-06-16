from django import forms
from django.contrib.auth.forms import AuthenticationForm


class CustomLoginForm(AuthenticationForm):

    attributes = {
        "class": "form-control",
        "placeholder": "Username",
        "id": "floatingInput",
    }
    username = forms.CharField(widget=forms.TextInput(attrs=attributes))
    password = forms.CharField(widget=forms.PasswordInput(attrs=attributes))
