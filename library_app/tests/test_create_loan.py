from datetime import UTC, datetime

import pytest

from library_app.services.create_loan import (
    DB_ALIAS,
    LOAN_REQUEST_STATUS_ID,
    LoanNumberUnavailable,
    create_loan,
    get_loan_number,
)


def test_get_loan_number_returns_value_when_stored_proc_called(mocker):
    mock_connection = mocker.patch("library_app.services.create_loan.connections")
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = ("LN12345",)

    mock_connection.__getitem__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
    result = get_loan_number()

    assert result == "LN12345"

    sql, params = mock_cursor.execute.call_args.args
    assert "EXEC qNextCode" in sql
    assert params == [35]


def test_get_loan_number_returns_none(mocker):
    """Test when stored proc fails and loan number doesn't bring a number"""
    # handle what happens when stored proc returns no number
    mock_connection = mocker.patch("library_app.services.create_loan.connections")
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_connection.__getitem__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
    with pytest.raises(LoanNumberUnavailable, match="returned no code"):
        get_loan_number()


def test_create_loan_saves_returns_loan_number_and_saves(mocker):
    fixed_now = datetime(2026, 3, 6, 12, 0, 0, tzinfo=UTC)

    mocker.patch(
        "library_app.services.create_loan.get_loan_number", return_value="LN12345"
    )
    mocker.patch(
        "library_app.services.create_loan.uuid.uuid4", return_value="test-uuid-123"
    )
    mocker.patch(
        "library_app.services.create_loan.timezone.now", return_value=fixed_now
    )

    mock_category_model = mocker.patch("library_app.services.create_loan.Category")
    mock_location_model = mocker.patch("library_app.services.create_loan.Location")
    mock_loan_request_class = mocker.patch(
        "library_app.services.create_loan.LoanRequest"
    )
    mock_atomic = mocker.patch("library_app.services.create_loan.transaction.atomic")

    mock_category = mocker.MagicMock()
    mock_location = mocker.MagicMock()
    mock_location.get_site_id.return_value = "SITE001"

    mock_category_model.objects.using.return_value.get.return_value = mock_category
    mock_location_model.objects.using.return_value.get.return_value = mock_location

    mock_loan_request = mocker.MagicMock()
    mock_loan_request_class.return_value = mock_loan_request

    result = create_loan(
        category_id="CAT001",
        location_id="LOC001",
        requester_name="John Smith",
        extension="1234",
        quantity=1,
        additional_info="Urgent request",
    )

    assert result == "LN12345"

    mock_loan_request_class.assert_called_once_with(
        loanrequestid="test-uuid-123",
        loanrequestcode="LN12345",
        requestdate=fixed_now,
        categoryid=mock_category,
        locationid="LOC001",
        requestedfor="John Smith- ext:1234",
        loanrequeststatusid=LOAN_REQUEST_STATUS_ID,
        loanrequestnotes="Urgent request",
        quantity=1,
        siteid="SITE001",
        creationdate=fixed_now,
    )
    mock_loan_request.full_clean.assert_called_once_with(validate_unique=False)
    mock_atomic.assert_called_once_with(using=DB_ALIAS)
    mock_loan_request.save.assert_called_once_with(using=DB_ALIAS)
