from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from cusas_app.models import Locations as USLocations

CUSAS_ADMIN_PERMISSION = "accounts.manage_profiles"


class CustomUser(AbstractUser):
    locations = models.ManyToManyField(USLocations, related_name="users", blank=True)
    department = models.CharField(max_length=250, blank=True, null=True)
    role = models.CharField(max_length=250, blank=True, null=True)

    @property
    def is_cusas_admin(self) -> bool:
        """True if this user holds the manage_profiles_permission."""
        permission = getattr(settings, "CUSAS_ADMIN_PERMISSION", CUSAS_ADMIN_PERMISSION)
        return self.is_authenticated and self.has_perm(permission)

    @property
    def all_locations(self):
        """
        Allow locations this user is associated with, whether directly
        or through the ultrasound profile

        :param self: Description
        """
        qs = USLocations.objects.none()

        # if user has any locations on the custom user
        qs = qs | self.locations.all()

        if hasattr(self, "profile"):
            qs = qs | self.profile.locations.all()

        return qs.distinct()

    def __str__(self):
        return self.username


class UltrasoundProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    locations = models.ManyToManyField(USLocations, related_name="profiles", blank=True)

    def __str__(self):
        return str(self.user)

    class Meta:
        permissions = [("manage_profiles", "Can manage CUSAS user profiles")]


class LibraryAdmin(models.Model):
    pass
