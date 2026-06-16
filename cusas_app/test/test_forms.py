import pytest

from cusas_app.forms import (
    MachineFaultForm,
    ProbeTestForm,
    ProbeTestFormSet,
    ReportFaultForm,
    UserManagementForm,
)

from .factories import MachineFactory, ProbeFactory


@pytest.mark.django_db
class TestUserManagementForm:
    def test_valid_form(self, location):
        form = UserManagementForm(
            data={
                "username": "testuser",
                "locations": [location.pk],
            }
        )
        assert form.is_valid(), form.errors

    def test_missing_username_is_invalid(self, location):
        form = UserManagementForm(data={"username": "", "location": [location.pk]})
        assert not form.is_valid()
        assert "username" in form.errors

    def test_missing_location_is_invalid(self):
        form = UserManagementForm(data={"username": "testuser", "locations": []})
        assert not form.is_valid()
        assert "locations" in form.errors

    def test_username_is_stripped_and_lowercased_in_view(self, location):
        """
        The view strips and changes the username to lowercase.
        Conirm view passes the raw value
        """
        form = UserManagementForm(
            data={"username": " TestUser ", "locations": [location.pk]}
        )
        assert form.is_valid()
        assert form.cleaned_data["username"] == "TestUser"


@pytest.mark.django_db
class TestProbeTestForm:
    def _form(self, **overrides):
        probe = ProbeFactory()
        data = {
            "probe_id": probe.id,
            "inspection": "pass",
            "reverb": 5.0,
            "noise": 50.0,
            "uniformity": "looks good",
            "report_fault": False,
        }
        data.update(overrides)
        return ProbeTestForm(data=data)

    def test_valid_pass_form(self):
        form = self._form()
        assert form.is_valid(), form.errors

    def test_not_present_clears_reverb_and_noise(self):
        """
        When 'not present' is chosen, reverb/noise are cleared even if supplied
        """

        form = self._form(
            inspection="not present", reverb=5.0, noise=50.0, uniformity="pass"
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["reverb"] is None
        assert form.cleaned_data["noise"] is None
        assert form.cleaned_data["uniformity"] is None

    def test_pass_requires_reverb(self):
        form = self._form(reverb=None)
        assert not form.is_valid(), form.errors
        assert "reverb" in form.errors

    def test_pass_requires_noise(self):
        form = self._form(noise=None)
        assert not form.is_valid()
        assert "noise" in form.errors

    def test_fail_allows_missing_reverb_and_noise(self):
        """On fail, user can leave the required field number blank and there
        wouldn't be an error"""
        form = self._form(inspection="fail", reverb=None, noise=None)
        assert form.is_valid(), form.errors

    def test_is_empty_when_nothing_filled(self):
        probe = ProbeFactory()
        form = ProbeTestForm(
            data={
                "probe_id": probe.id,
                "inspection": "",
                "reverb": "",
                "noise": "",
                "uniformity": "",
            }
        )
        form.is_valid()
        assert form.is_empty()

    def test_is_not_empty_when_inspection_set(self):
        form = self._form(inspection="pass")
        form.is_valid()
        assert not form.is_empty()


@pytest.mark.django_db
class TestProbeTestFormSet:
    def _management_data(self, total):
        return {
            "form-TOTAL_FORMS": str(total),
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        }

    def test_all_not_present_sing_probe_raises_error(self):
        probe = ProbeFactory()
        data = {
            **self._management_data(1),
            "form-0-probe_id": probe.id,
            "form-0-inspection": "not present",
        }
        formset = ProbeTestFormSet(data=data)
        assert not formset.is_valid()
        assert any("only probe" in str(e).lower() for e in formset.non_form_errors())

    def test_all_not_present_multiple_probes_raises_error(self):
        probe1, probe2 = ProbeFactory(), ProbeFactory()
        data = {
            **self._management_data(2),
            "form-0-probe_id": probe1.id,
            "form-0-inspection": "not present",
            "form-1-probe_id": probe2.id,
            "form-1-inspection": "not present",
        }
        formset = ProbeTestFormSet(data=data)
        assert not formset.is_valid()
        assert any("all probes" in str(e).lower() for e in formset.non_form_errors())

    def test_mixed_not_present_and_pass_is_valid(self):
        probe1, probe2 = ProbeFactory(), ProbeFactory()
        data = {
            **self._management_data(2),
            "form-0-probe_id": probe1.id,
            "form-0-inspection": "not present",
            "form-1-probe_id": probe2.id,
            "form-1-inspection": "pass",
            "form-1-reverb": "5.0",
            "form-1-noise": "50.0",
            'form-1-uniformity': 'looks good'
        }
        formset = ProbeTestFormSet(data=data)
        assert formset.is_valid(), {
            "form_errors": formset.errors,
            "non_form_errors": formset.non_form_errors(),
        }


class TestMachineFaultForm:
    def test_empty_form_is_valid(self):
        """Machine fault is optional - blank submission should be fine"""
        form = MachineFaultForm(data={"log_fault": ""})
        assert form.is_valid()

    def test_form_with_text_is_valid(self):
        form = MachineFaultForm(data={"log_fault": "Knob on machine missing"})

        assert form.is_valid()
        assert form.cleaned_data["log_fault"] == "Knob on machine missing"


@pytest.mark.django_db
class TestReportFaultForm:
    def test_valid_form_for_user_location(self, profile_user, machine):
        """User can only see machines in their location"""
        form = ReportFaultForm(
            user=profile_user,
            data={"asset_number": machine.pk, "reported_fault": "Probe cable frayed"},
        )

        assert form.is_valid(), form.errors

    def test_machine_outside_user_location_is_invalid(
        self, profile_user, other_location
    ):
        """Machines in location that user is not assigned should not show"""
        other_machine = MachineFactory(location=other_location)
        form = ReportFaultForm(
            user=profile_user,
            data={"asset_number": other_machine.pk, "reported_fault": "Not working"},
        )

        assert not form.is_valid()
        assert "asset_number" in form.errors

    def test_blank_reported_fault_is_invalid(self, profile_user, machine):
        form = ReportFaultForm(
            user=profile_user,
            data={"asset_number": machine.pk, "reported_fault": ""},
        )

        assert not form.is_valid()
