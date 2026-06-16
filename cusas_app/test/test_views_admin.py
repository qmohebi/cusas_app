import pytest
from django.urls import reverse

from .factories import UltrasoundProfileFactory, UserFactory


@pytest.mark.django_db
class TestProfileListView:
    url = reverse("cusas:user_management")

    def test_admin_user_can_access(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get(self.url)
        assert response.status_code == 200

    def test_unauthenticated_user_is_redirected(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert "/accounts/login" in response["Location"]

    def test_profile_user_without_admin_perm_gets_403(self, client, profile_user):
        client.force_login(profile_user)
        response = client.get(self.url)
        assert response.status_code == 403

    def test_get_loads_correct_template(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get(self.url)
        assert "cusas/cusas_user_management.html" in [
            t.name for t in response.templates
        ]

    def test_htmx_request_returns_partial_template(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get(self.url, HTTP_HX_REQUEST="true")
        assert response.status_code == 200
        assert "cusas/partials/_user_profile_table.html" in [
            t.name for t in response.templates
        ]

    def test_profiles_appear_in_context(self, client, admin_user, location):
        profile = UltrasoundProfileFactory(locations=[location])
        client.force_login(admin_user)
        response = client.get(self.url)
        assert profile in response.context["profiles"]


@pytest.mark.django_db
class TestAddProfileView:
    url = reverse("cusas:add_user")

    def _post(self, client, admin_user, data):
        client.force_login(admin_user)
        return client.post(self.url, data)

    def create_new_user_and_profile(self, client, admin_user, location):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        response = self._post(
            client, admin_user, {"username": "newstaff01", "location": [location.pk]}
        )
        assert response.status_code == 201
        assert User.objects.filter(username="newstaff01").exists()

    def test_username_is_lowercased(self, client, admin_user, location):
        from django.contrib.auth import get_user_model

        User = get_user_model()

        self._post(
            client,
            admin_user,
            {"username": "  NEWSTAFF02  ", "locations": [location.pk]},
        )
        assert User.objects.filter(username="newstaff02").exists()

    def test_existing_user_gets_location_updated(
        self, client, admin_user, location, other_location
    ):
        from accounts.models import UltrasoundProfile

        existing_user = UserFactory(username="existinguser")
        UltrasoundProfileFactory(user=existing_user, locations=[location])

        self._post(
            client,
            admin_user,
            {"username": "existinguser", "locations": [other_location.pk]},
        )
        profile = UltrasoundProfile.objects.get(user=existing_user)
        location_pks = list(profile.locations.values_list("pk", flat=True))
        assert other_location.pk in location_pks

    def test_missing_username_returns_422(self, client, admin_user, location):
        response = self._post(
            client, admin_user, {"username": "", "locations": [location.pk]}
        )

        assert response.status_code == 422

    def test_missing_locations_returns_422(self, client, admin_user):
        response = self._post(
            client, admin_user, {"username": "someuser", "locations": []}
        )
        assert response.status_code == 422

    def test_unauthenticated_post_is_redirected(self, client, location):
        response = client.post(
            self.url, {"username": "rogue", "locations": location.pk}
        )

        assert response.status_code == 302
