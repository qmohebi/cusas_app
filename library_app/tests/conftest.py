from datetime import datetime

import pytest
from django.urls import reverse
from pytest_factoryboy import register

from library_app.tests.factories import LoanCategoryFactory

register(LoanCategoryFactory)


@pytest.fixture
def library_loan_url():
    return reverse("library_app:equipment_library")


@pytest.fixture
def library_admin_url():
    return reverse("library_app:admin")


@pytest.fixture
def library_admin_sync_cat_url():
    return reverse("library_app:sync-category")


@pytest.fixture
def librar_admin_add_cat_url():
    return reverse("library_app:add_category")


@pytest.fixture
def fixed_date():
    return datetime(2026, 3, 9, 10, 0, 0)


@pytest.fixture
def mock_datetime(mocker, fixed_date):
    mock_dt = mocker.patch("library_app.views.datetime")
    mock_dt.now.return_value = fixed_date
    return mock_dt


@pytest.fixture
def mock_location_queryset(mocker):
    """Mocks the external equip db queryset in the forms __init__."""
    from library_app.models import Location

    mock_manager = mocker.MagicMock()
    (
        mock_manager.using.return_value.exclude.return_value.filter.return_value.order_by.return_value
    ) = Location.objects.none()
    mocker.patch("library_app.forms.Location.objects", mock_manager)
    return mock_manager


@pytest.fixture
def mock_bank_holiday(mocker):
    """Default to not a bank holiday - override per test with parameterised or re-patched"""
    return mocker.patch("library_app.views.is_bank_holiday", return_value=False)


@pytest.fixture
def mock_create_loan(mocker):
    return mocker.patch(
        "library_app.views.create_loan_from_form",
        return_value={"loan_id": 42},
    )


@pytest.fixture
def loan_categories(db):
    """Creates real LoanCategory objects for test taht need the category queryeset"""

    return LoanCategoryFactory.create_batch(3)


@pytest.fixture
def mock_location(mocker):
    """A fake Location object that passes ModelChoiceField validation"""
    from library_app.models import Location

    mock_loc = mocker.MagicMock()
    mock_loc.pk = 1
    mock_loc.locationshortname = "Test Location"

    qs_mock = mocker.MagicMock()
    qs_mock.get.return_value = mock_loc
    qs_mock.all.return_value = qs_mock
    qs_mock.__iter__.return_value = iter([mock_loc])
    qs_mock._result_cache = None
    qs_mock.using.return_value = qs_mock
    qs_mock.model = Location
    mock_manager = mocker.MagicMock()
    (
        mock_manager.using.return_value.exclude.return_value.filter.return_value.order_by.return_value
    ) = qs_mock
    mocker.patch("library_app.forms.Location.objects", mock_manager)

    return mock_loc


@pytest.fixture
def mock_category_form(mocker):
    """Prevent CategoryCreateForm from hitting the equip DB on instantiation"""
    from library_app.forms import CategoryCreateForm

    field = CategoryCreateForm.base_fields["category"]
    original_queryset = field.queryset

    qs_mock = mocker.MagicMock()
    field.queryset = qs_mock

    yield qs_mock

    field.queryset = original_queryset


@pytest.fixture
def view_mocks(mock_datetime, mock_location, mock_bank_holiday, mock_category_form):
    """
    Bundles all the fixtures for the library app loan view
    """
    return {
        "datetime": mock_datetime,
        "location_qs": mock_location,
        "bank_holiday": mock_bank_holiday,
        "equip_category_form": mock_category_form,
    }


@pytest.fixture
def valid_post_data(loan_categories, mock_location):
    return {
        "category": [str(cat.pk) for cat in loan_categories],
        "location": str(mock_location.pk),
        "requester_name": "John",
        "extension": 1234,
        "notes": "",
    }
