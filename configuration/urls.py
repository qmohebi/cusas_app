from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("mpce_services.urls", namespace="mpce_services")),
    path(
        "equipment-library/", include("library_app.urls", namespace="equipment_library")
    ),
    path("accounts/login/", auth_views.LoginView.as_view(), name='login'),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name='logout'),
    path("__reload__/", include("django_browser_reload.urls")),
    path("cusas/", include("cusas_app.urls", namespace="cusas")),
    path("select2/", include("django_select2.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
