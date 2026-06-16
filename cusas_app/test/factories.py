import datetime
from decimal import Decimal

import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from accounts.models import UltrasoundProfile
from cusas_app.models import (
    Fault,
    LocationQASchedule,
    Locations,
    Machine,
    Probe,
    StandardSchedule,
    TestResult,
)

User = get_user_model()


class LocationFactory(DjangoModelFactory):
    class Meta:
        model = Locations

    equip_location_id = factory.Sequence(lambda n: f"Location{n}")
    location_name = factory.Sequence(lambda n: f"Location: {n}")
    room = factory.Sequence(lambda n: f"Room {n}")


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save=True

    username = factory.Sequence(lambda n: f"user{n}")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    is_active = True

    @factory.post_generation
    def locations(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.locations.set(extracted)


class UltrasoundProfileFactory(DjangoModelFactory):
    class Meta:
        model = UltrasoundProfile
        skip_postgeneration_save=True

    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def locations(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.locations.set(extracted)


class MachineFactory(DjangoModelFactory):
    class Meta:
        model = Machine

    asset_number = factory.Sequence(lambda n: f"ASSET{n:04d}")
    model = factory.Faker("word")
    serial_number = factory.Sequence(lambda n: f"SN{n:06d}")
    equipment_id = factory.Sequence(lambda n: f"EQUIP{n:04d}")
    location = factory.SubFactory(LocationFactory)
    last_qa_date = None
    machine_qa_profile = None
    # next_qa_date = factory.LazyFunction(lambda: __import__('datetime').date.today() - __import__('datetime').timedelta(days=1))


class ProbeFactory(DjangoModelFactory):
    class Meta:
        model = Probe

    serial_number = factory.Sequence(lambda n: f"PROBE{n:04d}")
    probe_model = factory.Sequence(lambda n: f"ProbeModel{n}")
    equip_no = factory.Sequence(lambda n: f"EQ{n:04d}")
    equipment_id = factory.Sequence(lambda n: f"PEQUIP{n:04d}")
    machine = factory.SubFactory(MachineFactory)
    tolerance = Decimal("0.10")


class TestResultFactory(DjangoModelFactory):
    class Meta:
        model = TestResult

    probe = factory.SubFactory(ProbeFactory)
    user = factory.SubFactory(UserFactory)
    visual_inspection = True
    depth_reverb = 5.0
    noise_level_gain_value = 50.0
    uniformity = "Normal"
    result_date = factory.LazyFunction(datetime.date.today)
    is_baseline = False


class StandardScheduleFactory(DjangoModelFactory):
    class Meta:
        model = StandardSchedule

    name = factory.Sequence(lambda n: f"Schedule {n}")
    interval_days = 30
    is_active = True
    effective_from = None
    effective_to = None


class LocationQAScheduleFactory(DjangoModelFactory):
    class Meta:
        model = LocationQASchedule
        skip_postgeneration_save=True

    interval = 30
    is_active = True
    effective_from = None
    effective_to = None

    @factory.post_generation
    def location(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.location.set(extracted)


class FaultFactory(DjangoModelFactory):
    class Meta:
        model = Fault

    machine = factory.SubFactory(MachineFactory)
    user = factory.SubFactory(UserFactory)
    equip_job_no = factory.Sequence(lambda n: f"JOB{n:05d}")
