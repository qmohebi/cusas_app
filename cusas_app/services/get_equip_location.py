import logging
import json
from django.db import connections, transaction
from cusas_app.models import Locations

def update_location():
        with connections["equip"].cursor() as cursor:
            cursor.execute("""EXEC GetUSLocation""")
            result = cursor.fetchall()

        if not result or not result[0][0]:
            logging.error("No result received from GetUSLocation stored proc")

        try:
            data = json.loads(result[0][0])
        except json.JSONDecodeError as e:
            logging.error(e)

        with transaction.atomic():
            for item in data:
                Locations.objects.update_or_create(
                    equip_location_id=str(item["LocationId"]),
                    defaults={
                        "location_name": item.get("LocationShortName", ""),
                        "room": item.get("LocationText", ""),
                    },
                )