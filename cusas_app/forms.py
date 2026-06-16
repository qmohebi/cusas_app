from crispy_forms.helper import FormHelper
from django import forms
from django.forms import BaseFormSet, Form, formset_factory

from .models import Locations as USLocation
from .models import Machine


class UserManagementForm(Form):
    username = forms.CharField(
        label="Enter staff username",
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "e.g.usern00"}
        ),
    )

    locations = forms.ModelMultipleChoiceField(
        label="Select location from dropdown",
        queryset=USLocation.objects.all(),
        widget=forms.SelectMultiple(
            attrs={"class": "form-select select2", "required": "required"}
        ),
    )


class ProbeTestForm(forms.Form):
    """form to capture the test result of probe test"""

    probe_id = forms.IntegerField(widget=forms.HiddenInput)
    inspection = forms.ChoiceField(
        choices=[
            ("pass", "Pass"),
            ("fail", "Fail"),
            ("not present", "Not Present"),
        ],
        required=True,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        label="Visual Insepction",
    )
    uniformity = forms.CharField(
        required=False,
        empty_value=None,
        widget=forms.Textarea(
            attrs={
                "rows": 1,
                "class": "form-control-lg input-uniformity",
                "placeholder": "Comments",
            }
        ),
        label="Uniformity",
    )
    reverb = forms.FloatField(
        label="Depth of reverb (cm)",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control-lg input-reverb",
                "placeholder": "Value in cm",
            }
        ),
    )

    noise = forms.FloatField(
        label="Noise level gain (dB)",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control-lg input-noise",
                "placeholder": "Value in dB",
            }
        ),
    )
    report_fault = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Report an issue for this probe!",
    )

    def is_empty(self) -> bool:
        """Check to make sure user has filled the form"""
        cleaned = getattr(self, "cleaned_data", {})
        return not any(
            [
                cleaned.get("inspection"),
                cleaned.get("uniformity") is not None,
                cleaned.get("reverb") is not None,
                cleaned.get("noise") is not None,
                cleaned.get('report_fault'),
            ]
        )


    def clean(self):
        """
        conditionally set the required field based on inspection result.

        -if inspection=='not present': allow the rest of the form to be empty
        -else reverb and noise must be filled.
        """

        cleaned = super().clean()
        inspection = cleaned.get("inspection")
        reverb = cleaned.get("reverb")
        noise = cleaned.get("noise")
        uniformity = cleaned.get('uniformity')

        # stirp the form if not present is selected.
        if inspection == "not present":
            cleaned["reverb"] = None
            cleaned["noise"] = None
            cleaned['uniformity'] = None
            cleaned["baseline"] = False
            cleaned["threshold"] = False

            return cleaned

        # This ensure that only when pass is selected to enforce the rule
        # where something fails, the user can either input or leave blank
        # and the form submits
        if inspection == "pass":
            if reverb is None:
                self.add_error("reverb", "This field is required.")
            if noise is None:
                self.add_error("noise", "This field is required")
            if uniformity is None:
                self.add_error("uniformity", "This field is required")

        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_labels = False


class BaseProbeTestFormSet(BaseFormSet):
    """
    BaseFormset used for displaying error when user
    selects Not present on all the probes on the machine.

    """

    def clean(self):
        super().clean()

        if any(self.errors):
            return

        inspections = []
        for f in self.forms:
            # manage the can delete forms
            if getattr(self, "can_delete", False) and f.cleaned_data.get("DELETE"):
                continue
            inspections.append(f.cleaned_data.get("inspection"))

        # validation for when not present is select on a machine that has one probe
        # or when the machine has multiple probes and not present is selected on all probes.
        inspections = [f.cleaned_data.get("inspection") for f in self.forms]
        if inspections and all(i == "not present" for i in inspections):
            if len(inspections) == 1:
                raise forms.ValidationError(
                    "You can't complete QA as the only probe is marked as 'Not Present'"
                )
            raise forms.ValidationError(
                "You can't complete QA as all probes are marked as 'Not Present'"
            )


ProbeTestFormSet = formset_factory(ProbeTestForm, formset=BaseProbeTestFormSet, extra=0)


class MachineFaultForm(forms.Form):
    log_fault = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": "form-control",
                "placeholder": "Add any issues you found with machine",
            }
        ),
        label="General machine fault",
    )


class ReportFaultForm(forms.Form):
    asset_number = forms.ModelChoiceField(
        label="Machine",
        empty_label="Select a machine",
        required=True,
        queryset=Machine.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    reported_fault = forms.CharField(
        label="Reported fault",
        required=True,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your fault here...",
                "row": 2,
                "rows": 5,
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_show_labels = False
        # filter the equipment that a user can search and report
        # fault for.
        if user is not None:
            self.fields["asset_number"].queryset = Machine.objects.filter(
                location__in=user.all_locations
            )
