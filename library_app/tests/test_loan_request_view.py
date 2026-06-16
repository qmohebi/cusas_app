import pytest
import json
from library_app.views import OpeningHoursContextMixin


@pytest.mark.django_db
def test_get_returns_200(client, library_loan_url, view_mocks):
    response = client.get(library_loan_url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_get_uses_correct_template(client, library_loan_url, view_mocks):
    """This is purely for regression testing to ensure
    any template changes results in error."""
    response = client.get(library_loan_url)
    assert "library_app/loan_request.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_context_opening_hours(client, library_loan_url, view_mocks):
    opening_hour = OpeningHoursContextMixin.OPENING_HOUR
    closing_hour = OpeningHoursContextMixin.CLOSING_HOUR

    response = client.get(library_loan_url)

    assert response.context["opening_hour"] == opening_hour
    assert response.context["closing_hour"] == closing_hour


@pytest.mark.django_db
@pytest.mark.parametrize("is_bh", [True, False])
def test_bank_holiday_flag(client, library_loan_url, view_mocks, mocker, is_bh):
    """Test bank holiday returns correctly"""

    mocker.patch("library_app.views.is_bank_holiday", return_value=is_bh)
    response = client.get(library_loan_url)
    assert response.context["bank_holiday"] == is_bh


@pytest.mark.django_db
def test_loan_request_view_get_split_categories(
    client, loan_category_factory, library_loan_url, view_mocks
):
    normal_category = loan_category_factory(is_permanent_loan=False)
    permanent_category = loan_category_factory(is_permanent_loan=True)
    response = client.get(library_loan_url)

    assert normal_category in response.context["loan_item"]
    assert permanent_category in response.context["permanent_loan"]
    assert normal_category not in response.context["permanent_loan"]


@pytest.mark.django_db
def test_valid_post_returns_200(
    client, library_loan_url, view_mocks, valid_post_data, mock_create_loan
):
    response = client.post(library_loan_url, data=valid_post_data)
    assert response.status_code == 200

@pytest.mark.django_db
def test_invalid_post_response_shape(client, library_loan_url, view_mocks):
    response = client.post(library_loan_url, data={})
    data = json.loads(response.content)
    assert data['status']=='error'
    assert 'error' in data