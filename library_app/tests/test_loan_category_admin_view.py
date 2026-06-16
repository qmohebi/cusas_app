import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse


def add_permission(user):
    User = get_user_model()
    perm = Permission.objects.get(codename="manage_loan_categories")
    user.user_permissions.add(perm)
    return User.objects.get(pk=user.pk)


class TestLibraryAdminView:
    url = reverse("library_app:library-admin")

    def test_unauthorised_user_is_redirected(self, client):
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_permission_is_forbidden(self, client, user):
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code in (302, 403)

    def test_user_with_permission_can_access(self, client, user):
        user = add_permission(user)
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestCategoryCreateView:
    url = reverse("library_app:add_category")

    def test_unauthenticated_user_is_redirected(self, client):
        response = client.get(self.url)
        assert response.status_code == 302

    def test_user_without_permission_is_forbidden(self, client, user):
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code in (302, 403)

    def test_user_with_permission_sees_form(self, client, user, mock_category_form):
        user = add_permission(user)
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert "form" in response.context


class TestSyncCategoryView:
    url = reverse("library_app:sync_categories")

    def test_unauthenticated_user_is_redirected(self, client):
        response = client.post(self.url)
        assert response.status_code == 302

    def test_user_without_permission_is_forbidden(self, user, client):
        client.force_login(user)
        response = client.post(self.url)
        assert response.status_code in (302, 403)

    def test_user_with_permission_can_trigger_syn(self, mocker, user, client):
        user = add_permission(user)
        client.force_login(user)
        mocker.patch(
            "library_app.views.get_categories.get_library_category",
            return_value=[],
        )

        response = client.post(self.url, HTTP_HX_REQUEST="true")
        assert response.status_code == 200
