from datetime import date

import requests


def is_bank_holiday(date_to_check: date) -> bool:
    """
    the function calls the gov.uk api for bank holidays
    and if the date provided is bank holiday, it returns true
    """

    url = "https://www.gov.uk/bank-holidays/england-and-wales.json"

    response = requests.get(url)
    json_response = response.json()


    return any(event["date"] == date_to_check.isoformat() for event in json_response["events"])
