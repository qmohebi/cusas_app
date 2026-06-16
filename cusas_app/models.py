from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connections, models, transaction
from django.db.models import F, Index, Q

from .services.equip import create_repair_job, get_child_assets

logger = logging.getLogger(__name__)


class Locations(models.Model):
    # TODO map this to eQuip's location table
    equip_location_id = models.CharField(max_length=200, unique=True)
    location_name = models.CharField(max_length=200)
    room = models.CharField(max_length=200)

    def __str__(self):
        return self.location_name


class StandardSchedule(models.Model):
    """Reusable standard schedule that can be assinged to a machine
    no link to a machine or a location
    e.g. Standard 30 days"""

    name = models.CharField(max_length=120, unique=True)
    interval_days = models.PositiveBigIntegerField()
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            Index(fields=["is_active"]),
            Index(fields=["effective_from", "effective_to"]),
        ]

    constraints = [
        models.CheckConstraint(
            name="schedule_profile_window_ok",
            condition=Q(effective_to__isnull=True)
            | Q(effective_from__isnull=True)
            | Q(effective_to__gte=F("effective_from")),
        )
    ]

    def __str__(self):
        return f"{self.name}({self.interval_days}d)"

    def is_effective_on(self, date: date) -> bool:
        return (
            self.is_active
            and (self.effective_from is None or self.effective_from <= date)
            and (self.effective_to is None or self.effective_to >= date)
        )


class LocationQASchedule(models.Model):
    """Global QA rule per location, applies to all the machines in that location"""

    # profile = models.ForeignKey(
    #     StandardSchedule, on_delete=models.PROTECT, related_name="location_rules"
    # )
    locations = models.ManyToManyField(
        Locations, related_name="location_qa_schedules", blank=True
    )
    interval_days = models.PositiveBigIntegerField()
    effective_from = models.DateField(blank=True, null=True)
    effective_to = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            Index(fields=["is_active"]),
            Index(fields=["effective_from", "effective_to"]),
        ]

    constraints = [
        models.CheckConstraint(
            name="location_schedule_wind_ok",
            condition=Q(effective_to__isnull=True)
            | Q(effective_from__isnull=True)
            | Q(effective_to__gte=F("effective_from")),
        )
    ]

    def __str__(self):
        locations = ", ".join(
            self.locations.values_list("location_name", flat=True)[:3]
        )
        return f"{locations}: {self.interval_days} days"

    def clean(self):
        # Prevent overlapping location rules using *different* profiles for the same location/time window
        if not self.pk:
            return

        start = self.effective_from or date.min
        end = self.effective_to or date.max
        overlapping = (
            LocationQASchedule.objects.exclude(pk=self.pk)
            .filter(is_active=True)
            .filter(
                Q(effective_from__isnull=True) | Q(effective_from__lte=end),
                Q(effective_to__isnull=True) | Q(effective_to__gte=start),
            )
        )
        location_ids = set(self.locations.values_list("id", flat=True))
        if location_ids:
            conflict = overlapping.filter(locations__in=location_ids).distinct()
            if conflict.exists():
                raise ValidationError(
                    "Overlapping location schedule exists for one or more locations."
                )

    def locations_list(self):
        """helper to show list of locations for given schedule"""
        names = self.locations.values_list("location_name", flat=True)
        return ", ".join(names) or "ALL locations"


class Machine(models.Model):
    # TODO merge machine and probe and create an equipment table

    asset_number = models.CharField(max_length=100, unique=True)
    machine_name = models.CharField(max_length=200, blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    machine_room = models.CharField(max_length=250, blank=True, null=True)
    location = models.ForeignKey(
        Locations,
        to_field="equip_location_id",
        db_column="equip_location_id",
        null=True,
        on_delete=models.CASCADE,
        related_name="machines",
    )
    last_qa_date = models.DateField(blank=True, null=True)
    next_qa_date = models.DateField(blank=True, null=True, editable=False)
    installation_date = models.DateField(blank=True, null=True)
    equipment_id = models.CharField(max_length=250)
    machine_qa_profile = models.ForeignKey(
        StandardSchedule,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="machines",
    )

    class Meta:
        indexes = [
            Index(fields=["asset_number"]),
            Index(fields=["location"]),
            Index(fields=["next_qa_date"]),
        ]

    def __str__(self):
        return self.asset_number

    def get_qa_interval_days(self, on_date: date | None = None) -> list | None:
        """Check if specific machine has a schedule
        if not, look for location that machine belongs and get active schedule for that location
        if not get the global generic days"""
        on_date = on_date or date.today()

        if self.machine_qa_profile and self.machine_qa_profile.is_effective_on(on_date):
            return self.machine_qa_profile.interval_days

        if self.location_id:
            location_rules = (
                LocationQASchedule.objects.filter(
                    is_active=True,
                )
                .filter(
                    Q(effective_from__isnull=True) | Q(effective_from__lte=on_date),
                    Q(effective_to__isnull=True) | Q(effective_to__gte=on_date),
                )
                .filter(Q(locations=self.location))
                .order_by("-effective_from", "-pk")
            )

            # take interval from the location rule itself
            rule = location_rules.first()
            if rule:
                return rule.interval_days
        # if all failes, fall back on either what is in the settings
        # or 30 days
        return getattr(settings, "DEFAULT_QA_INTERVAL_DAYS", 30)

    def calculate_next_due_date(self, on_date: date | None = None):
        """Calculate the next QA date"""
        if not self.last_qa_date:
            return None
        interval = self.get_qa_interval_days(on_date=on_date)
        return self.last_qa_date + timedelta(days=interval) if interval else None

    def save(self, *args, **kwargs) -> None:
        next_due_date = self.calculate_next_due_date()
        self.next_qa_date = next_due_date
        super().save(*args, **kwargs)

class Service(models.Model):
    # service_id = models.CharField(max_length=200, primary_key=True)
    service_name = models.CharField(max_length=200)

    def __str__(self):
        return self.service_name


class MachineTesters(models.Model):
    # testers_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, null=True, on_delete=models.CASCADE)


class Probe(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name="probe")
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    probe_model = models.CharField(max_length=200)
    equip_no = models.CharField(max_length=250)
    equipment_id = models.CharField(max_length=250)
    tolerance = models.DecimalField(
        blank=True,
        null=True,
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.10"),
        help_text="QA Tolerance for probe",
    )

    def __str__(self):
        return self.probe_model


# TODO cleanup of the class method to a service
class TestResult(models.Model):
    UNITE_CHOICES = [
        ("NS", "Not started"),
        ("IP", "In progress"),
        ("C", "Completed successfully"),
    ]

    probe = models.ForeignKey(Probe, on_delete=models.CASCADE, related_name="qa_result")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    visual_inspection = models.BooleanField(
        null=True, blank=True, verbose_name="Visual Inspection"
    )
    uniformity = models.TextField(null=True, blank=True)
    depth_reverb = models.FloatField(null=True, blank=True)
    noise_level_gain_value = models.FloatField(null=True, blank=True)
    result_date = models.DateField()
    is_baseline = models.BooleanField(default=False)

    @classmethod
    def get_last_qa_result(cls, probe: "Probe"):
        """
        returns the most recent test result for this porbe
        """
        return cls.objects.filter(probe=probe).order_by("-result_date", "-id").first()

    @classmethod
    def check_tolerance(cls, probe, field_name: str, value: float) -> Optional[bool]:
        """
        Compares the value of probe field to the last stored test result
        if within tolerance of the probe:

        returns:
        True -> within tolerance
        False -> out of tolerance
        None -> no previous result to compare

        """
        last_result = cls.get_last_qa_result(probe=probe)
        if not last_result:
            return None

        reference_value = getattr(last_result, field_name)
        if reference_value is None or value is None:
            return None

        reference_dec = Decimal(str(reference_value))
        value_dec = Decimal(str(value))

        tolerance = getattr(probe, "tolerance", None)
        # if no tolerance in the probe
        if tolerance is None:
            tolerance = Decimal("0.10")
        else:
            tolerance = Decimal(str(tolerance))

        lower_limit = reference_dec * (Decimal("1.0") - tolerance)
        upper_limit = reference_dec * (Decimal("1.0") + tolerance)

        return lower_limit <= value_dec <= upper_limit

    @classmethod
    def create_test_result(cls, *, probe, user, cleaned_data) -> TestResult:
        """
        Creates Test result for the given probe,
        checks if Probe has baseline and set that
        checks if probe wihtin tolerance and gives appropriate error message

        :param probe: instance of probe
        :param user: logged user
        :param cleaned_data: clean data
        """
        inspection = cleaned_data.get("inspection")

        # This is when a probe is not on the machine,
        # even if a user puts values in the form, it shouldn't
        # create a test result.
        if inspection not in ("pass", "fail"):
            raise ValueError(
                "create_test_result must be called with pass or fail inspection"
            )
        last_result = cls.get_last_qa_result(probe=probe)
        is_baseline = last_result is None

        if inspection == "pass":
            visual_inspection = True
        else:
            visual_inspection = False

        return cls.objects.create(
            probe=probe,
            user=user,
            visual_inspection=visual_inspection,
            uniformity=cleaned_data.get("uniformity"),
            depth_reverb=cleaned_data.get("reverb"),
            noise_level_gain_value=cleaned_data.get("noise"),
            result_date=date.today(),
            is_baseline=is_baseline,
        )


class Fault(models.Model):
    UNIT_CHOICES = [
        ("NS", "Not started"),
        ("IP", "In progress"),
        ("C", "Completed successfully"),
    ]

    machine = models.ForeignKey(
        Machine, null=True, blank=True, on_delete=models.CASCADE, related_name="faults"
    )
    probe = models.ForeignKey(
        Probe, on_delete=models.CASCADE, null=True, blank=True, related_name="faults"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    equip_job_no = models.CharField(max_length=50, db_index=True)

    def clean(self):
        if not self.machine or not self.probe:
            raise ValidationError("Fault must have either a machine or a probe")

    @classmethod
    def create_fault(
        cls, *, user, machine: Machine = None, probe: Probe = None, fault_text=None
    ) -> Fault:
        """
        Creates a repair job on eQuip, gets the job number and creates
        a Fault.

        :param user: authenticated user
        :param machine: Machine the fault needs to be logged for
        :type machine: Machine instance
        :param probes: Probe that needs fault created for
        :type probes: Probes
        :param reported_fault: what was the fault
        :return: Fault instance
        :rtype: Fault
        """

        if machine is None and probe is None:
            raise ValueError("create_fault requires either a machine or probe")

        equipment_id = machine.equipment_id if machine else probe.equipment_id
        # if machine is not None:
        #     equipment_id = machine.equipment_id
        # else:
        #     equipment_id = probe.equipment_id

        caller = f"{user.first_name} {user.last_name}"

        job_no = create_repair_job(
            equipment_id=equipment_id, reported_fault=fault_text, caller_fullname=caller
        )
        job_code = str(job_no) if job_no is not None else None

        return cls.objects.create(
            machine=machine, probe=probe, user=user, equip_job_no=job_code
        )


class Job(models.Model):
    jobid = models.CharField(db_column="JobId", primary_key=True, max_length=50)
    jobcode = models.CharField(
        db_column="JobCode", max_length=50, blank=True, null=True, unique=True
    )  # Field name made lowercase.
    jobshortname = models.CharField(
        db_column="JobShortName", max_length=255, blank=True, null=True
    )  # Field name made lowercase.
    joblongname = models.TextField(
        db_column="JobLongName", blank=True, null=True
    )  # Field name made lowercase.
    jobdescription = models.TextField(
        db_column="JobDescription", blank=True, null=True
    )  # Field name made lowercase.
    jobnotes = models.TextField(
        db_column="JobNotes", blank=True, null=True
    )  # Field name made lowercase.
    jobissuedate = models.DateTimeField(
        db_column="JobIssueDate", blank=True, null=True
    )  # Field name made lowercase.

    creationdate = models.DateTimeField(
        db_column="CreationDate", blank=True, null=True
    )  # Field name made lowercase.

    jobtypeid = models.ForeignKey(
        "Jobtype", models.DO_NOTHING, db_column="JobTypeId", blank=True, null=True
    )  # Field name made lowercase.
    jobstatusid = models.ForeignKey(
        "Jobstatus", models.DO_NOTHING, db_column="JobStatusId", blank=True, null=True
    )  # Field name made lowercase.

    caller = models.CharField(
        db_column="Caller", max_length=255, blank=True, null=True
    )  # Field name made lowercase.
    callertel = models.CharField(
        db_column="CallerTel", max_length=50, blank=True, null=True
    )  # Field name made lowercase.

    techcontactid = models.CharField(
        db_column="TechContactId", max_length=50, blank=True, null=True
    )  # Field name made lowercase.
    reportedfault = models.TextField(
        db_column="ReportedFault", blank=True, null=True
    )  # Field name made lowercase.
    faultfound = models.TextField(db_column="FaultFound", blank=True, null=True)

    workdone = models.TextField(
        db_column="WorkDone", blank=True, null=True
    )  # Field name made lowercase.
    workstartdate = models.DateTimeField(
        db_column="WorkStartDate", blank=True, null=True
    )  # Field name made lowercase.
    workenddate = models.DateTimeField(
        db_column="WorkEndDate", blank=True, null=True
    )  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = "Job"


class Jobstatus(models.Model):
    jobstatusid = models.CharField(
        db_column="JobStatusId", primary_key=True, max_length=50
    )
    jobstatuscode = models.CharField(
        db_column="JobStatusCode", max_length=50, blank=True, null=True
    )
    jobstatusshortname = models.CharField(
        db_column="JobStatusShortName", max_length=255, blank=True, null=True
    )
    jobstatuslongname = models.TextField(
        db_column="JobStatusLongName", blank=True, null=True
    )
    jobstatusclassid = models.CharField(
        db_column="JobStatusClassId", max_length=50, blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = "JobStatus"


class Jobstatusclass(models.Model):
    jobstatusclassid = models.CharField(
        db_column="JobStatusClassId", primary_key=True, max_length=50
    )
    jobstatusclasscode = models.CharField(
        db_column="JobStatusClassCode", max_length=50, blank=True, null=True
    )
    jobstatusclassshortname = models.CharField(
        db_column="JobStatusClassShortName", max_length=255, blank=True, null=True
    )
    jobstatusclasslongname = models.TextField(
        db_column="JobStatusClassLongName", blank=True, null=True
    )
    jobstatusclassdescription = models.TextField(
        db_column="JobStatusClassDescription", blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = "JobStatusClass"


class Jobtype(models.Model):
    jobtypeid = models.CharField(db_column="JobTypeId", primary_key=True, max_length=50)
    jobtypecode = models.CharField(
        db_column="JobTypeCode", max_length=50, blank=True, null=True
    )
    jobtypeshortname = models.CharField(
        db_column="JobTypeShortName", max_length=255, blank=True, null=True
    )
    jobtypelongname = models.TextField(
        db_column="JobTypeLongName", blank=True, null=True
    )
    jobtypedescription = models.TextField(
        db_column="JobTypeDescription", blank=True, null=True
    )
    modificationdate = models.DateTimeField(
        db_column="ModificationDate", blank=True, null=True
    )
    inactive = models.BooleanField(db_column="Inactive", blank=True, null=True)

    class Meta:
        managed = False
        db_table = "JobType"
