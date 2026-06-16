import logging

from django.conf import settings
from django.db import connections, transaction

from library_app.models import LoanCategory

logger = logging.getLogger(__name__)


def get_library_category() -> dict:
    """
    Looks on eQuip for assets that have library status is one of equipment library
    and gets the category id, and categoryshortname
    """
    if "equip" not in settings.DATABASES:
        raise RuntimeError(
            "Database alias 'equip' is not configured in settings.DATABASES. "
            "Check env vars / settings split."
        )

    sql = """
        SELECT DISTINCT CategoryId, CategoryShortName
        FROM dbo.vbAsset
        WHERE EquipmentLibraryStatusId IN (%s, %s, %s)
    """
    params = ("WWW2", "WWW3", "WWW4")

    logger.info("Fetching categories from 'equip'...")
    try:
        with connections["equip"].cursor() as cursor:
            cursor.execute(sql, params)
            data = cursor.fetchall()
    except Exception:
        logger.exception("Query against 'equip' failed")

    created_count = 0
    updated_count = 0

    with transaction.atomic(using="default"):
        for cat_id, cat_name in data:
            _, was_created = LoanCategory.objects.using("default").update_or_create(
                category_id=str(cat_id),
                defaults={"category_name": cat_name},
            )
            if was_created:
                created_count += 1
            else:
                updated_count += 1
    return {"rows": len(data), "created": created_count, "updated": updated_count}
