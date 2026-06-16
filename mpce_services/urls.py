from django.urls import path

from datetime import datetime, date
from django.contrib.auth import views as auth_views
from .views import HomePageView, StaffOnlyView, debug_meta, mecr_redirect

app_name = "mpce_services"

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("mpce-staff", StaffOnlyView.as_view(), name="mpce_staff_view"),
    path("debug-meta/", debug_meta, name="debug_meta"),
    path("MECR", mecr_redirect),
]
