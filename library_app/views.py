import logging
from datetime import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, FormView, ListView, UpdateView

from .forms import (
    CategoryCreateForm,
    CategoryManagementForm,
    LoanRequestForm,
    LogisticsRequestForm,
)
from .models import LoanCategory
from .services import get_categories
from .services.check_bank_holiday import is_bank_holiday
from .services.create_loan import LoanCreationError, create_loan_from_form
from .tasks import send_library_request_bleep

logger = logging.getLogger(__name__)


class OpeningHoursContextMixin:
    """Set the opening and closing hours and
    pass as context to the tempalte"""

    OPENING_HOUR = 3
    CLOSING_HOUR = 24

    def get_context_data(self, **kwargs):
        now = datetime.now()
        context = super().get_context_data(**kwargs)
        context["opening_hour"] = self.OPENING_HOUR
        context["closing_hour"] = self.CLOSING_HOUR
        context["day"] = now.isoweekday()
        # if now.isoweekday() in [6, 7]:
        #     context["weekend"] = True
        # else:
        #     context["weekend"] = False
        context["bank_holiday"] = is_bank_holiday(date_to_check=now.date())
        return context


class LoanRequestView(OpeningHoursContextMixin, FormView):
    # model = Category
    template_name = "library_app/loan_request.html"
    form_class = LoanRequestForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = context["form"].fields["category"].queryset
        context["loan_form"] = LoanRequestForm()
        context["loan_item"] = queryset.filter(is_permanent_loan=False)
        context["permanent_loan"] = queryset.filter(is_permanent_loan=True)
        return context

    def form_valid(self, form):
        try:
            loan_data = create_loan_from_form(form.cleaned_data)
            location = form.cleaned_data["location"]
            location_name = location.locationshortname
            send_library_request_bleep.delay(
                loan_data=loan_data,
                location_name=location_name
            )

        except LoanCreationError as exc:
            logger.warning(
                "Failed to create a loan request %s",
                exc,
                extra={
                    "error_code": exc.error_code,
                    "category": str(form.cleaned_data.get("category")),
                    "location": str(form.cleaned_data.get("location")),
                },
            )
            return render(
                self.request,
                "library_app/partials/_error_modal.html",
                {
                    "modal_id": "loanErrorModal",
                    "modal_title": "Request Failed",
                    "modal_items": [exc.user_message],
                },
                status=exc.http_status,
            )

        return JsonResponse(
            {
                "status": "success",
                "loan_data": loan_data,
            }
        )

    def form_invalid(self, form):
        return JsonResponse(
            {
                "status": "error",
                "error": form.errors.get_json_data(),
            },
            status=400,
        )


class LogisticsRequestView(FormView):
    template_name = "library_logistics.html"
    form_class = LogisticsRequestForm
    success_url = "./"
    login_url = "./success"

    def form_valid(self, form):
        form.create_request()
        return super().form_valid(form)


class LibraryAdmin(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "library_app/library_administration.html"
    model = LoanCategory
    permission_required = "library_app.manage_loan_categories"
    # raise_exception = True # comment this out to redirect to login else it will show 403
    context_object_name = "categories"


class CategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = LoanCategory
    permission_required = "library_app.manage_loan_categories"
    # raise_exception = True # comment this out to redirect to login else it will show 403
    form_class = CategoryManagementForm
    template_name = "library_app/partials/_category_edit_modal.html"

    # success_url = reverse_lazy("library_app:library-admin")

    def is_htmx(self):
        return self.request.headers.get("HX-Request") == "true"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()

        if self.is_htmx():
            return HttpResponse(
                render_to_string(self.template_name, context, request=request)
            )

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()

        if self.request.headers.get("HX-Request") == "true":
            resp = HttpResponse(status=204)  # no content, don't swap anything
            resp["HX-Redirect"] = reverse("library_app:library-admin")
            return resp

        return super().form_valid(form)


@require_POST
@login_required
@permission_required("library_app.manage_loan_categories", raise_exception=True)
def get_equip_categories(request):
    """
    Sync function that gets equipment library categories from eQuip
    """
    if request.headers.get("HX-Request") != "true":
        return HttpResponse(status=400)

    try:
        get_categories.get_library_category()
    except Exception as e:
        return HttpResponse(str(e), status=500)
    categories = LoanCategory.objects.all().order_by("is_active")
    return render(
        request,
        "library_app/partials/_category_rows.html",
        {"categories": categories},
        status=200,
    )


class CategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = LoanCategory
    permission_required = "library_app.manage_loan_categories"
    # raise_exception = True
    form_class = CategoryCreateForm
    template_name = "library_app/partials/_category_create_modal.html"

    def is_htmx(self):
        return self.request.headers.get("HX-Request") == "true"

    def get(self, request, *args, **kwargs):
        self.object = None  # this ensures the get doesn't throw attribute error.
        context = self.get_context_data()
        if self.is_htmx():
            return HttpResponse(
                render_to_string(self.template_name, context, request=request)
            )
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        if self.is_htmx():
            resp = HttpResponse(status=204)
            resp["HX-Redirect"] = reverse("library_app:library-admin")
            return resp
        return super().form_valid(form)
