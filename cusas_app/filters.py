import django_filters
from accounts.models import UltrasoundProfile
from django.db.models import Q

from .models import Machine


class ProfileFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(
        method="filter_by_user_or_location", label="search"
    )

    class Meta:
        model = UltrasoundProfile
        fields = []

    def filter_by_user_or_location(self, queryset, name, value):
        """
        Filter queryset by user or by locations"""

        return queryset.filter(
            Q(user__username__icontains=value)
            | Q(locations__location_name__icontains=value)
        ).distinct()


class DeviceFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(
        method="device_property_filter", label="device_search"
    )

    class Meta:
        model = Machine
        fields = []

    def device_property_filter(self, queryset, name, value):
        return queryset.filter(
            Q(model__icontains=value) | Q(location__location_name__icontains=value)
        ).distinct()
