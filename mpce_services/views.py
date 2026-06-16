from django.http import HttpResponse, HttpResponseRedirect
from .models import MPCESections
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from library_app.views import OpeningHoursContextMixin


class HomePageView(OpeningHoursContextMixin, ListView):
    model = MPCESections
    template_name = "index.html"
    context_object_name = "services"


class StaffOnlyView(LoginRequiredMixin, TemplateView):
    template_name = "mpce_admin.html"

    # def dispatch(self, request, *args, **kwargs):
    #     remote_user = request.META.get("REMOTE_USER")
    #     if remote_user and not request.user.is_authenticated:
    #         user = authenticate(remote_user=remote_user)
    #         if user:
    #             login(request, user)
    #     return super().dispatch(request, *args, **kwargs)

    # def get(self, request, *args, **kwargs):
    #     remote_user = request.META.get('REMOTE_USER')
    #     # print(request.META)
    #     if remote_user:
    #         return HttpResponse(f"REMOTE_USER header found: {remote_user}")
    #     else:
    #         return HttpResponse("No REMOTE_USER header found")


def debug_meta(request):
    return HttpResponse("<br>".join(f"{k}: {v}" for k, v in request.META.items()))


def mecr_redirect(request):
    return HttpResponseRedirect("http://stg1equip01/Login.aspx?ReturnUrl=%2f")
