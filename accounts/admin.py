from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, UltrasoundProfile


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ["username", "first_name", "last_name", "department", "role"]


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UltrasoundProfile)
