import csv
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import formats
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import FormView, ListView, TemplateView, View
from django_filters.views import FilterView

from accounts.models import UltrasoundProfile

from .filters import DeviceFilter, ProfileFilter
from .forms import (
    MachineFaultForm,
    ProbeTestFormSet,
    ReportFaultForm,
    UserManagementForm,
)
from .mixins import CUSASAdminPermissionMixin, CUSASProfileRequiredMixin
from .models import Fault, Machine, Probe, TestResult
from .services import create_fault, get_equip_job_info

User = get_user_model()  # This ensures the add user refrences the django auth


@method_decorator(ensure_csrf_cookie, name="dispatch")
class ProfileListView(CUSASAdminPermissionMixin, ListView):
    """lists all the profiles and the locations assigned to them"""

    # TODO add link to individual profile so it can be amended.
    queryset = UltrasoundProfile.objects.all()
    template_name = "cusas/cusas_user_management.html"
    context_object_name = "profiles"

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = ProfileFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filterset
        context["form"] = UserManagementForm()
        context["show_services"] = False

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("HX-Request") == "true":
            return render(
                self.request, "cusas/partials/_user_profile_table.html", context
            )
        return super().render_to_response(context, **response_kwargs)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class AddProfileView(CUSASAdminPermissionMixin, View):
    """gets username and locations,
    creates profile and username in the user table
    if user exists, adds the new location to that profile
    if user doesn't exist, still creates the user but gives unusable password
    password is then updated with ldap sign in."""

    def post(self, request, *args, **kwargs):
        form = UserManagementForm(request.POST)
        if not form.is_valid():
            msg = (
                '<div class="alert alert-danger" role="alert">'
                "Could not save user. Check you have a username and at least one location."
                "</div>"
            )
            oob = '<div id="addUserFlag" data-added="0" hx-swap-oob="true"></div>'
            return HttpResponse(msg + oob, status=422)

        username = form.cleaned_data["username"].strip().lower()
        locations = form.cleaned_data["locations"]

        # creates a user profile with given username, gives a unusable password
        # the password is then updated when user logs in with ldap.
        # providing the profile username is accurate, ldap would update the password
        try:
            with transaction.atomic():
                # 1) Get or create local auth user (no local password; LDAP will auth)
                user, created_user = User.objects.get_or_create(
                    username=username,
                    defaults={"is_active": True},
                )
                if created_user:
                    user.set_unusable_password()  # Here we set the password as temp as user will login with ldap
                    user.save(update_fields=["password"])

                # Get or create the profile
                profile, _ = UltrasoundProfile.objects.get_or_create(user=user)

                # Assign locations (replace set)
                profile.locations.set(list(locations))

        except IntegrityError as e:
            msg = (
                '<div class="alert alert-danger" role="alert">'
                "Could not save profile due to a constraint error. "
                f"Details: {e}"
                "</div>"
            )
            oob = '<div id="addUserFlag" data-added="0" hx-swap-oob="true"></div>'
            return HttpResponse(msg + oob, status=409)
        except Exception:
            msg = (
                '<div class="alert alert-danger" role="alert">'
                "Unexpected error while saving the profile."
                "</div>"
            )
            oob = '<div id="addUserFlag" data-added="0" hx-swap-oob="true"></div>'
            return HttpResponse(msg + oob, status=500)

        msg = (
            '<div class="alert alert-success" role="alert">'
            "User saved successfully."
            "</div>"
        )
        oob = '<div id="addUserFlag" data-added="1" hx-swap-oob="true"></div>'
        return HttpResponse(msg + oob, status=201)


class DownloadCSVView(CUSASProfileRequiredMixin, View):
    def get(self, request, asset_number):
        machine = get_object_or_404(Machine, asset_number=asset_number)
        asset_number = machine.asset_number
        query_set = (
            TestResult.objects.filter(probe__machine__asset_number=asset_number)
            .select_related("probe", "probe__machine", "user")
            .order_by("-result_date")
        )
        filename = f"{machine.model}_{machine.serial_number}_{machine.machine_room}"
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f"attachment; filename={filename}_qa_result.csv"
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "Machine Asset No",
                "Probe Serial No",
                "Tester Fullname",
                "Visual Inspection",
                "Uniformity",
                "Depth Reverb",
                "Noise Level",
                "result_date",
            ]
        )
        for row in query_set:
            probe_sn = getattr(row.probe, "serial_number")
            full_name = f"{getattr(row.user, 'first_name', '')} {getattr(row.user, 'last_name', '')}".strip()

            writer.writerow(
                [
                    asset_number,
                    probe_sn,
                    full_name,
                    row.visual_inspection,
                    row.uniformity,
                    row.depth_reverb,
                    row.noise_level_gain_value,
                    row.result_date,
                ]
            )
        return response


class CusasIndexView(CUSASProfileRequiredMixin, TemplateView):
    """shows cusas main page with data for each machine according to the due date
    probe results and displays to the user"""

    template_name = "cusas/cusas.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["modal_payload"] = self.request.session.pop(
            "success_modal_payload", None
        )
        user = self.request.user
        # Fault.update_job_from_equip()
        # show due today or before as red
        # show due in 2 days as amber
        # who due in 3-5 days as green
        # anove above 5 days don't show
        # TODO move this to a config file and replace the days to RAG 
        today = date.today()    
        two_days = today + timedelta(days=2)
        five_days = today + timedelta(days=5)

        # Base queryset: ONLY due/overdue/never-tested machines (all locations)
        qs = Machine.objects.filter(
            Q(next_qa_date__lt=today)
            | Q(next_qa_date__range=(today, five_days))
            | Q(last_qa_date__isnull=True)
        )

        # This user see ALL locations
        can_see_all = user.is_superuser or user.has_perm("accounts.manage_profiles")

        # Only apply location filter if the user CANNOT see all locations
        if can_see_all:
            machines = qs.order_by("next_qa_date")
        else:
            machines = qs.filter(location__in=user.all_locations).order_by(
                "next_qa_date"
            )

        faults_qs = Fault.objects.all()

        if not can_see_all:
            faults_qs = faults_qs.filter(
                Q(machine__location__in=user.all_locations)
                | Q(probe__machine__location__in=user.all_locations)
            )

        faults_qs = faults_qs.select_related("machine", "probe").order_by("-id")

        faults = get_equip_job_info.get_latest_equip_job_info(faults_qs)

        context.update(
            {
                "machines": machines,
                "today": today,
                "five_days": five_days,
                "two_days": two_days,
                "faults": faults,
                "show_services": False,  # removes services from nav-bar
            }
        )
        return context


class ProbeTestView(CUSASProfileRequiredMixin, View):
    """show a machine and all its probes
    to allow user to run QA on them."""

    template_name = "cusas/probes_test.html"

    def get_machine(self, asset_number: str) -> Machine:
        return get_object_or_404(
            Machine.objects.select_related("location"), asset_number=asset_number
        )

    def get(self, request, asset_number):
        machine = self.get_machine(asset_number=asset_number)
        probes = list(machine.probe.all())
        initial = [{"probe_id": probe.id} for probe in probes]
        formset = ProbeTestFormSet(initial=initial)
        machine_form = MachineFaultForm()

        # self._check_baseline_rules(probes=probes, formset=formset)

        rows = list(zip(probes, formset.forms))

        context = {
            "machine": machine,
            "rows": rows,
            "formset": formset,
            "machine_form": machine_form,
            "show_services": False,
        }
        return render(request, self.template_name, context)

    def post(self, request, asset_number):
        machine = self.get_machine(asset_number=asset_number)
        probes = list(machine.probe.all())
        probe_map = {probe.id: probe for probe in probes}

        formset = ProbeTestFormSet(request.POST)
        machine_form = MachineFaultForm(request.POST)

        if not formset.is_valid() or not machine_form.is_valid():
            messages.error(request, "Please correct the error below.")
            rows = list(zip(probes, formset.forms))
            return render(
                request,
                self.template_name,
                {
                    "machine": machine,
                    "rows": rows,
                    "formset": formset,
                    "machine_form": machine_form,
                },
            )
        machine_fault = machine_form.cleaned_data.get("log_fault")
        no_probe_form_changes = all(f.is_empty() for f in formset.forms)
        no_machine_fault = not machine_fault

        if no_probe_form_changes and no_machine_fault:
            messages.error(
                request, "Record will not be saved as no changes have been made"
            )

            rows = list(zip(probes, formset.forms))
            return render(
                request,
                self.template_name,
                {
                    "machine": machine,
                    "rows": rows,
                    "formset": formset,
                    "machine_form": machine_form,
                },
            )
        created_faults = []
        qa_probe_sn = []
        # used for faults picked up on probe
        fault_reasons = []

        logged_user = request.user
        with transaction.atomic():
            # machine fault
            if machine_fault:
                fault = create_fault.create_fault(
                    machine=machine, user=logged_user, fault_text=machine_fault
                )
                created_faults.append(
                    {
                        "machine": machine.asset_number,
                        "job_no": fault.equip_job_no,
                    }
                )

            # probe fault
            for form in formset:
                if form.is_empty():
                    continue
                cd = form.cleaned_data
                probe = probe_map.get(cd["probe_id"])

                if probe is None:
                    continue

                visual_inspection = cd.get("inspection")

                if visual_inspection == "not present":
                    continue

                depth_reverb = cd.get("reverb")
                noise_level_gain = cd.get("noise")
                user_report_fault = cd.get("report_fault")
                print(user_report_fault)
                uniformity = cd.get("uniformity")

                reverb_tolerance = None
                noise_tolerance = None

                if visual_inspection == "fail":
                    fault_reasons.append("Visual inspection failed")

                # check whether  depth reverb value is in tolearance or not
                if depth_reverb is not None:
                    reverb_tolerance = TestResult.check_tolerance(
                        probe=probe, field_name="depth_reverb", value=depth_reverb
                    )

                # check whether noise level value is in tolearance or not
                if noise_level_gain is not None:
                    noise_tolerance = TestResult.check_tolerance(
                        probe=probe,
                        field_name="noise_level_gain_value",
                        value=noise_level_gain,
                    )
                # if there is an issue with reverb or noise level entry
                if reverb_tolerance is False:
                    fault_reasons.append("Depth reverb out of tolerance")

                if noise_tolerance is False:
                    fault_reasons.append("Noise level gain is out of tolerance")

                # ensur there is data in both the fields
                # if data in fields even if failed, create test result
                if depth_reverb is not None and noise_level_gain is not None:
                    TestResult.create_test_result(
                        probe=probe, user=logged_user, cleaned_data=cd
                    )
                    # save the probe sn to build message
                    qa_probe_sn.append(probe.serial_number)

                # check if the reported fault is ticked or system picked a fault
                if user_report_fault:
                    fault = Fault.create_fault(
                        probe=probe,
                        user=logged_user,
                        fault_text=f"""User reported issue during QA.\
                        Visual inspection = {visual_inspection} Uniformaity: {uniformity} Reverb: {depth_reverb} Noise: {noise_level_gain}""",
                    )
                    created_faults.append(
                        {
                            "probe_sn": probe.serial_number,
                            "job_no": fault.equip_job_no,
                        }
                    )

                elif fault_reasons:
                    fault = Fault.create_fault(
                        probe=probe,
                        user=logged_user,
                        fault_text="; ".join(fault_reasons),
                    )
                    created_faults.append(
                        {
                            "probe_sn": probe.serial_number,
                            "job_no": fault.equip_job_no,
                        }
                    )
        fault_logged_message = "with Medical Physics to follow up."
        next_qa_date = machine.next_qa_date
        next_qa_date_str = (
            formats.date_format(next_qa_date, "DATE_FORMAT") if next_qa_date else "-"
        )
        message_items = [
            format_html(
                "Probe: {} QA completed<br>Next QA Date: <span class='fw-bold'>{}</span>",
                probe_sn,
                next_qa_date_str,
            )
            for probe_sn in (qa_probe_sn or [])
        ] + [
            format_html(
                "Fault logged for: <strong>{}</strong> {}",
                f"Machine {f['machine']}"
                if "machine" in f
                else f"Probe {f['probe_sn']}",
                fault_logged_message,
            )
            for f in created_faults
        ]

        modal_payload = {
            "modelId": "successModal",
            "title": "QA Completed!",
            "items": message_items,
            "redirectUrl": reverse("cusas:cusas_home"),
        }
        initial = [{"probe_id": probe.id} for probe in probes]
        formset = ProbeTestFormSet(initial=initial)
        machine_form = MachineFaultForm()
        # self._check_baseline_rules(probes=probes, formset=formset)

        rows = list(zip(probes, formset.forms))

        return render(
            request,
            self.template_name,
            {
                "machine": machine,
                "rows": rows,
                "formset": formset,
                "machine_form": machine_form,
                "modal_payload": modal_payload,
                "modal_id": "successModal",
            },
        )


class ProbeFieldCheckView(View):
    template_name = "partials/_cusas_field_error.html"
    FIELD_MAP = {"reverb": "depth_reverb", "noise": "noise_level_gain_value"}

    def post(self, request, field, *args, **kwargs):
        """on this post request, values entered by the user on
        the cusas form is checked against previous result and
        if the result is out of tolerance, htmx error is sent.
        """
        # the field on the form is different to that on model,
        # mapping here to the correct one
        model_field = self.FIELD_MAP.get(field)

        if not model_field:
            return render(request, self.template_name, {"error": "no model field"})

        prefix = "form"
        try:
            total_forms = int(request.POST.get(f"{prefix}-TOTAL_FORMS", 0))
        except ValueError:
            total_forms = 0

        probe_id = None
        value = None
        # print(request.POST.dict())
        # to understand how the below code works, enable the print above
        # this will show you how formset and the probe and fields are rendered
        # by django. we use the key value to walk
        # all rows in the formset and find the one for this field
        # Walk all rows in the formset and find the one for this field
        for i in range(total_forms):
            field_key = f"{prefix}-{i}-{field}"
            probe_key = f"{prefix}-{i}-probe_id"

            if field_key in request.POST:
                candidate_value = request.POST.get(field_key)
                candidate_probe_id = request.POST.get(probe_key)

                # only interested in entered values and probe for it
                if candidate_value not in (None, ""):
                    value = float(candidate_value)
                    probe_id = candidate_probe_id
                    break

        if not probe_id or value in (None, ""):
            return render(request, self.template_name, {"error": "no probe id"})

        probe = get_object_or_404(Probe, pk=probe_id)
        try:
            num_value = float(value)
        except ValueError:
            return render(request, self.template_name, {"error": ""})

        in_tolerance = TestResult.check_tolerance(
            probe=probe, field_name=model_field, value=num_value
        )

        if in_tolerance is None:
            error = ""
        elif in_tolerance is False:
            error = "Out of tolerance, consider reporting!"
        else:
            error = ""

        return render(request, self.template_name, {"error": error})


def FilterDevice(request, filter):
    """
    Filter used for admin device table to filter based on search items
    """

    filterset = DeviceFilter(request.GET, queryset=Machine.objects.all())
    machines = filterset.qs

    context = {"filter": filterset, "machines": machines}

    if request.heards.get("HX-request") == "true":
        return render(request, "cusas/partials/_cusas_device_table.html", context)

    return render(request, "")


class LibraryView(CUSASAdminPermissionMixin, FilterView):
    """
    Lists all ultrasound devices and allows for filter
    based on user's search.
    """

    template_name = "cusas/cusas_library.html"
    # ultrasound = Machine.objects.all()
    model = Machine
    context_object_name = "machines"
    filterset_class = DeviceFilter

    def get_template_names(self):
        if self.request.headers.get("HX-Request") == "true":
            return ["cusas/partials/_cusas_device_table.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_services"] = False
        context["filter"] = self.filterset
        return context


class ReportFaultView(CUSASProfileRequiredMixin, FormView):
    template_name = "cusas/cusas_report_fault.html"
    form_class = ReportFaultForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_services"] = False
        return context

    def form_valid(self, form):
        user = self.request.user
        machine = form.cleaned_data["asset_number"]
        reported_fault = form.cleaned_data["reported_fault"]

        fault = create_fault.create_fault(
            user=user,
            machine=machine,
            fault_text=reported_fault,
        )

        modal_items = [
            f"Fault logged for machine {machine}",
            f"Job reference: {fault.equip_job_no}",
        ]

        empty_form = self.form_class(user=user)

        # return emtpy form on close of modal
        context = self.get_context_data(
            form=empty_form,
            show_success_modal=True,
            modal_payload={
                "modalId": "successModal",
                "title": "Fault Logged",
                "items": modal_items,
                "show_services": False,
            },
        )
        return self.render_to_response(context=context)

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
