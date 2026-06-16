from django.contrib import admin

from .models import (
    Fault,
    LocationQASchedule,
    Locations,
    Machine,
    MachineTesters,
    Probe,
    Service,
    StandardSchedule,
    TestResult,
)

admin.site.register(MachineTesters)
# admin.site.register(Locations)
# admin.site.register(TestResult)
admin.site.register(Service)


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ("probe", "result_date")


@admin.register(Probe)
class ProbesAdmin(admin.ModelAdmin):
    list_display = ("machine", "serial_number", "probe_model", "equip_no")
    list_filter = ("equip_no",)


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = (
        "asset_number",
        "machine_name",
        "manufacturer",
        "model",
        "machine_room",
        "serial_number",
        "location",
        "last_qa_date",
        "next_qa_date",
    )
    # list_filter = ("asset_number",)


@admin.register(Locations)
class LocationsAdmin(admin.ModelAdmin):
    list_display = (
        "equip_location_id",
        "location_name",
    )
    list_filter = ("location_name",)


@admin.register(StandardSchedule)
class StandardScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "interval_days",
        "is_active",
        "effective_from",
        "effective_to",
    )
    list_filter = ("is_active",)


@admin.register(LocationQASchedule)
class LocationQAScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "locations_list",
        "interval_days",
        "is_active",
        "effective_from",
        "effective_to",
    )
    filter_horizontal = ("locations",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("locations")


@admin.register(Fault)
class FaultAdmin(admin.ModelAdmin):
    list_display = (
        "machine",
        "probe",
    )
