import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from accounts.models import UltrasoundProfile

from .factories import (
    LocationFactory,
    MachineFactory,
    ProbeFactory,
    UltrasoundProfileFactory,
    UserFactory,
)

User = get_user_model()


@pytest.fixture
def location(db):
    return LocationFactory()


@pytest.fixture
def other_location(db):
    return LocationFactory()


@pytest.fixture
def plain_user(db):
    """
    Authenticated user with no proble or no admin permission
    """
    return UserFactory()


@pytest.fixture
def profile_user(db, location):
    user = UserFactory()
    UltrasoundProfileFactory(user=user, locations=[location])
    return user


@pytest.fixture
def admin_user(db, location):
    user = UserFactory()
    content_type = ContentType.objects.get_for_model(UltrasoundProfile)
    perm = Permission.objects.get(codename="manage_profiles", content_type=content_type)
    user.user_permissions.add(perm)
    user = User.objects.get(pk=user.pk)
    return user


@pytest.fixture
def superuser(db):
    user = UserFactory(is_superuser=True, is_staff=True)
    return user


@pytest.fixture
def machine(db, location):
    return MachineFactory(location=location)


@pytest.fixture
def machine_with_probe(db, location):
    """
    A machine with two probes
    """
    m = MachineFactory(location=location)
    ProbeFactory(machine=m)
    ProbeFactory(machine=m)
    return m
