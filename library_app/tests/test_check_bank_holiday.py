from datetime import date

from library_app.services.check_bank_holiday import is_bank_holiday


def test_bank_holiday_date_true(mocker):
    """
    Function to test whether
    given date is bank holiday in UK or not
    """
    date_to_check = date(2026, 4, 3)
    mock_data = {
        "division": "england-and-wales",
        "events": [
            {
                "title": "Good Friday",
                "date": "2026-04-03",
                "notes": "",
                "bunting": False,
            },
            {
                "title": "Easter Monday",
                "date": "2026-04-06",
                "notes": "",
                "bunting": False,
            },
        ],
    }
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = mock_data

    mocker.patch(
        "library_app.services.check_bank_holiday.requests.get",
        return_value=mock_response,
    )

    assert is_bank_holiday(date_to_check) is True


def test_bank_holiday_date_false(mocker):
    """test when given date is not bank holiday
    that it returns False"""
    date_to_check = date(2026, 4, 4)
    mock_data = {
        "division": "england-and-wales",
        "events": [
            {
                "title": "Good Friday",
                "date": "2026-04-03",
                "notes": "",
                "bunting": False,
            },
            {
                "title": "Easter Monday",
                "date": "2026-04-06",
                "notes": "",
                "bunting": False,
            },
        ],
    }
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = mock_data

    mocker.patch(
        "library_app.services.check_bank_holiday.requests.get",
        return_value=mock_response,
    )

    assert is_bank_holiday(date_to_check) is False
