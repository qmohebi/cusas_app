import logging

from django.core.management.base import BaseCommand, CommandError

from cusas_app.services.get_equip_asset import get_equip_asset

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync ultrasound machines and probes from eQuip"

    def handle(self, *args, **options):
        self.stdout.write("Starting eQuip asset sync...")

        try:
            get_equip_asset()
        except Exception as e:
            logger.exception("eQuip asset sync failed")
            raise CommandError(f"eQuip asset sync failed: {e}") from e

        self.stdout.write(
            self.style.SUCCESS("eQuip asset sync completed successfully.")
        )
