from django.db import transaction

from cusas_app.models import Fault, Machine, Probe
from cusas_app.services.equip import create_repair_job


@transaction.atomic
def create_fault(
    *, user, machine: Machine = None, probe: Probe = None, fault_text=None
) -> Fault:
    """
    Creates a repair job on eQuip, gets the job number and creates
    a Fault for the ultrasound.

    :param user: authenticated user
    :param machine: Machine the fault needs to be logged for
    :type machine: Machine instance
    :param probes: Probe that needs fault created for
    :type probes: Probe instance
    :param reported_fault: fault with the device
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

    return Fault.objects.create(
        machine=machine, probe=probe, user=user, equip_job_no=job_code
    )
