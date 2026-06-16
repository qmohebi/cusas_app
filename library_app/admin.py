from django.contrib import admin

from .models import LoanCategory


@admin.register(LoanCategory)
class LoanCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "category_name",
        "category_id",
        "display_name",
        "is_permanent_loan",
        "is_active",
    )
