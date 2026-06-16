from django.db.models.signals import m2m_changed, post_save, post_delete
from django.dispatch import receiver

from .models import LocationQASchedule, Machine, StandardSchedule, TestResult


@receiver(post_save, sender=LocationQASchedule)
def recalculate_on_location_schedule_save(sender, instance, **kwargs):
    equip_ids = list(instance.locations.values_list("equip_location_id", flat=True))
    if equip_ids:
        machines = Machine.objects.filter(location_id__in=equip_ids)
    else:
        machines = Machine.objects.all()

    for machine in machines:
        machine.save()


@receiver(m2m_changed, sender=LocationQASchedule.locations.through)
def recalculate_on_location_schedule_m2m(sender, instance, action, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        equip_ids = list(instance.locations.values_list("equip_location_id", flat=True))
        qs = (
            Machine.objects.all()
            if not equip_ids
            else Machine.objects.filter(location_id__in=equip_ids)
        )
        for mahcine in qs:
            mahcine.save()


@receiver(post_save, sender=StandardSchedule)
def recalculate_on_profile_change(sender, instance, **kwargs):
    """'on change of Standard QA Schedule"""
    for machine in instance.machines.all():
        machine.save()


def _update_machine_qa_dates_for_machine(machine: Machine):
    """
    recalculates the last qa date and next qa date for a machine
    based on qa result of the probe

    :param machine: Machine instance
    :type machine: Machine
    """

    if machine is None:
        return

    latest_result = (
        TestResult.objects.filter(probe__machine=machine)
        .order_by("-result_date", "-id")
        .first()
    )
    if latest_result:
        machine.last_qa_date = latest_result.result_date
    else:
        machine.last_qa_date = None

    machine.save(update_fields=["last_qa_date", "next_qa_date"])


@receiver(post_save, sender=TestResult)
def update_machine_qa_date_on_save(sender, instance: TestResult, **kwargs):
    """
    on saving the a new TestResult, the machine last qa date and next qa date
    gets updated.

    :param sender: the model that triggers that change
    """
    machine = instance.probe.machine
    if machine:
        _update_machine_qa_dates_for_machine(machine=machine)


@receiver(post_delete, sender=TestResult)
def update_machine_qa_dates_on_delete(sender, instance: TestResult, **kwargs):
    """
    on deleting a TestResult, the machine last qa date and next qa date
    gets updated.

    :param sender: the model that triggers that change
    """
    machine = instance.probe.machine
    if machine:
        _update_machine_qa_dates_for_machine(machine=machine)
