# CusasUserManagementView
from django.urls import path

from .views import (
    AddProfileView,
    CusasIndexView,
    DownloadCSVView,
    LibraryView,
    ProbeFieldCheckView,
    ProbeTestView,
    ProfileListView,
    ReportFaultView,
)

app_name = "cusas_app"

urlpatterns = [
    path("", CusasIndexView.as_view(), name="cusas_home"),
    path("qa/<str:asset_number>/", ProbeTestView.as_view(), name="qa"),
    path("library/", LibraryView.as_view(), name="library"),
    # path("accounts/login/", auth_views.LoginView.as_view()),
    path("user-management", ProfileListView.as_view(), name="user_management"),
    path("user-management/add/", AddProfileView.as_view(), name="add_user"),
    path(
        "htmx/probe-check/<str:field>/",
        ProbeFieldCheckView.as_view(),
        name="probe-field-check",
    ),
    path("report-fault/", ReportFaultView.as_view(), name="report_fault"),
    path(
        "machines/<str:asset_number>/results.csv/",
        DownloadCSVView.as_view(),
        name="export_result",
    ),
]
