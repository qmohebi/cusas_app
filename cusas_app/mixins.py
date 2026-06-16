from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from accounts.models import CUSAS_ADMIN_PERMISSION, UltrasoundProfile


class HtmxMixin:
    """Adds HTMX detection helpers to any view"""

    def _header(self, name: str, default=None):
        if hasattr(self.request, "headers"):
            return self.request.headers.get(name, default)
        meta_key = "HTTP_" + name.upper().replace("-", "_")
        return self.request.META.get(meta_key, default)

    def _is_htmx(self) -> bool:
        return self._header("HX-Request") == "true"


def is_cusas_admin(user) -> bool:
    """
    checks if the given user is part of cusas_admin gropu
    """
    permission = getattr(settings, "CUSAS_ADMIN_PERMISSION", "accounts.manage_profiles")
    if not user.is_authenticated:
        return False

    return user.has_perm(permission)


class CUSASAdminPermissionMixin(HtmxMixin, LoginRequiredMixin, UserPassesTestMixin):
    """
    Grants access only to users with manage_profile permissioins (i.e. members of cusas_admin group)
    Handles HTMX and full-page response separately for both unauthenticated and unauthorised cases.
    """

    permission_required = CUSAS_ADMIN_PERMISSION
    login_url = "/accounts/login"
    # login_url = reverse_lazy("accounts:login")
    raise_exception = False

    def test_func(self):
        """check authentication and permission"""
        return self.request.user.has_perm(self.permission_required)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            if self._is_htmx():
                html = render_to_string(
                    "partials/_auth_required_modal.html", {}, request=self.request
                )
                return HttpResponse(html, status=200)
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )

        # if self._is_htmx():
        #     html = render_to_string(
        #         "partials/_permission_denied_modal.html", {}, request=self.request
        #     )
        #     return HttpResponse(html, status=200)

        return render(
            self.request,
            "cusas/cusas_403.html",
            {"support_email": "ultrasoundphysics@stgeorges.nhs.uk"},
            status=403,
        )


class CUSASProfileRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Grants access to cusas_admin users unconditionally, and to any
    authenticated user who has been assigned an UltrasoundProfile.
    """

    def test_func(self) -> bool:
        user = self.request.user
        return (
            user.is_cusas_admin or UltrasoundProfile.objects.filter(user=user).exists()
        )

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return render(
            self.request,
            "cusas/cusas_403.html",
            {"support_email": "ultrasoundphysics@stgeorges.nhs.uk"},
            status=403,
        )
