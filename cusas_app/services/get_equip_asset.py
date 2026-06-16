import logging

from django.db import connections, transaction

from cusas_app.models import Machine, Probe
from cusas_app.services.equip import get_child_assets

logger = logging.getLogger(__name__)


def get_equip_asset() -> None:
    """
    Update or create ultrasound asset from eQuip
    This service is used to sync the machine data from eQuip
    ensure the location sync has happened first before running this.
    """

    with connections["equip"].cursor() as cursor:
        cursor.execute("""
                        SELECT 
                            EquipmentCode, 
                            SerialNo, 
                            BrandShortName, 
                            ModelShortName, 
                            LocationId, 
                            InstallationDate,
                            EquipmentId,
                            LocationText
                        FROM
                            vbAsset
                        WHERE 
                            CategoryShortName LIKE '%Ultrasound Scanner%' 
                            AND CustomerShortName LIKE '%SGH%'
                            AND Inactive = 0 """)
        rows = cursor.fetchall()

        if not rows:
            logging.error("No rows returned from views")
            return
        with transaction.atomic():
            for (
                EquipmentCode,
                SerialNo,
                BrandShortName,
                ModelShortName,
                LocationId,
                InstallationDate,
                EquipmentId,
                Locationtext,
            ) in rows:
                name = room = ""
                if isinstance(Locationtext, str):
                    parts = str(Locationtext).split("-", 1)

                    if len(parts) == 2:
                        room, name = (part.strip() for part in parts)
                    else:
                        name = ""
                        room = ""
                defaults = {
                    "asset_number": EquipmentCode or "",
                    "serial_number": SerialNo or "",
                    "manufacturer": BrandShortName or "",
                    "model": ModelShortName or "",
                    "installation_date": InstallationDate or None,
                    "equipment_id": EquipmentId or None,
                    "machine_name": name,
                    "machine_room": room,
                }
                if LocationId:
                    defaults["location_id"] = str(LocationId)

                machine, _ = Machine.objects.update_or_create(
                    asset_number=str(EquipmentCode),
                    defaults=defaults,
                )

                get_children_probe(equipment_id=EquipmentId, machine=machine)


def get_children_probe(equipment_id: str, machine: Machine) -> None:
    """
    Get the children probe for a given ultrasound machine

    """

    data = get_child_assets(parent_id=equipment_id)
    if not data:
        return

    for item in data:
        equip_no = item["EquipmentCode"]
        if not equip_no:
            continue

        serial_no = item.get("SerialNo")
        model = item.get("ModelShortName")
        equipment_id = item.get("EquipmentId")

        Probe.objects.update_or_create(
            equip_no=str(equip_no),
            defaults={
                "serial_number": serial_no or "",
                "probe_model": model or "",
                "machine": machine,
                "equipment_id": equipment_id,
            },
        )
