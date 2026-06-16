from django.urls import path

from . import views
from .views import (
    CategoryCreateView,
    CategoryUpdateView,
    LibraryAdmin,
    LoanRequestView,
    LogisticsRequestView,
)

app_name = "library_app"

urlpatterns = [
    path("", LoanRequestView.as_view(), name="equipment_library"),
    path(
        "library-logistics/",
        LogisticsRequestView.as_view(),
        name="library-logistics",
    ),
    path("admin/", LibraryAdmin.as_view(), name="library-admin"),
    path(
        "loan_categories/<int:pk>/modal/",
        CategoryUpdateView.as_view(),
        name="loan_category_edit_modal",
    ),
    path("admin/sync-category/", views.get_equip_categories, name="sync_categories"),
    path("admin/add-category/", CategoryCreateView.as_view(), name="add_category"),
    # path('category-management', LibraryCategoryManagementView.as_view(), name='category-management')
]
