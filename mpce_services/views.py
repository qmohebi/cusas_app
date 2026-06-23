from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import ListView, TemplateView

from .models import MPCESections


class HomePageView(ListView):
    model = MPCESections
    template_name = "index.html"
    context_object_name = "services"


class StaffOnlyView(LoginRequiredMixin, TemplateView):
    template_name = "mpce_admin.html"


def debug_meta(request):
    return HttpResponse("<br>".join(f"{k}: {v}" for k, v in request.META.items()))


def mecr_redirect(request):
    return HttpResponseRedirect("http://stg1equip01/Login.aspx?ReturnUrl=%2f")
