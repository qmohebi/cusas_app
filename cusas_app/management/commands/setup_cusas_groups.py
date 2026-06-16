from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates the cusas_admin gropu and assigns the manage_profiles permission"

    def handle(self, *args, **options):
        try:
            perm = Permission.objects.get(codename="manage_profiles")
        except Permission.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(
                    "Permission 'manage_profiles' not found. "
                    "Ensure migrations have been run first"
                )
            )
            return
        group, created = Group.objects.get_or_create(name="cusas_admin")
        group.permissions.add(perm)
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    "Created group 'cusas_admin' with manage_profiles permissions"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Group 'cusas_admin' already exisits - permissions confirmed"
                )
            )
