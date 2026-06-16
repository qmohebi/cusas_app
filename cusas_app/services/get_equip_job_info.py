from datetime import timedelta

from django.utils import timezone

from cusas_app.models import Job

DONE_CLASSES = {"CLOSED", "FINISHED", "CANCELLED"}


def get_latest_equip_job_info(faults, completed_within_days=10):
    """
    Gets latest job information from eQuip for all the faults

    :param faults: cusas faults
    """
    faults = list(faults)

    job_codes = [f.equip_job_no for f in faults if f.equip_job_no]
    if not job_codes:
        return faults

    # completed job cutoff point
    cutoff = timezone.now() - timedelta(days=completed_within_days)

    done_job_codes = set(
        Job.objects.using("equip")
        .filter(jobcode__in=job_codes)
        .filter(workenddate__isnull=False, workenddate__lt=cutoff)
        .filter(jobstatusid__jobstatusclassid__in=DONE_CLASSES)
        .values_list("jobcode", flat=True)
    )
    faults = [fault for fault in faults if fault.equip_job_no not in done_job_codes]
    if not faults:
        return []

    remaining_jobs = {fault.equip_job_no for fault in faults if fault.equip_job_no}

    jobs = (
        Job.objects.using("equip")
        .select_related("jobstatusid")
        .filter(jobcode__in=remaining_jobs)
        .only(
            "jobcode",
            "reportedfault",
            "workdone",
            "creationdate",
            "workenddate",
            "jobstatusid",
            "jobstatusid__jobstatusshortname",
            "jobstatusid__jobstatusclassid",
        )
    )

    job_map = {j.jobcode: j for j in jobs}

    for f in faults:
        j = job_map.get(f.equip_job_no)
        f.reportedfault = getattr(j, "reportedfault", None)
        f.workdone = getattr(j, "workdone", "")
        f.creationdate = getattr(j, "creationdate", None)
        f.jobstatus_shortname = (
            j.jobstatusid.jobstatusshortname if j and j.jobstatusid_id else None
        )

    return faults
