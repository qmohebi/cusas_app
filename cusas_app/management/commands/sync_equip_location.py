import logging

from django.core.management.base import BaseCommand, CommandError

from cusas_app.services.get_equip_location import update_location

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync ultrasound machines and probes from eQuip"

    def handle(self, *args, **options):
        self.stdout.write("Starting eQuip asset sync...")

        try:
            update_location()
        except Exception as e:
            logger.exception("Update location from eQuip failed.")
            raise CommandError(f"Update location failed: {e}") from e

        self.stdout.write(self.style.SUCCESS("Update completed successfully."))
