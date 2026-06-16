import uuid
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import DatabaseError, connections, transaction
from django.utils import timezone

from library_app.models import Category, LoanRequest, Location

"""Utility class for creating a loan request"""

DB_ALIAS = "equip"
LOAN_REQUEST_STATUS_ID = "09CB8F87-8386-482E-8120-A99011358FD9"

LOAN_CREATION_ERROR_MSG = "We are unable to take your request, please bleep our library team on: xxxx."


class LoanCreationError(Exception):
    """Raised when a loan request cannot be created."""

    error_code = "loan_creation_failed"
    user_message = LOAN_CREATION_ERROR_MSG
    http_status = 500


class LoanNumberUnavailable(LoanCreationError):
    """Raise this error when loan number not available"""

    error_code = "loan_number_unavailable"
    user_message = LOAN_CREATION_ERROR_MSG
    http_status = 503


def get_loan_number():
    """execute stored procedure on eQuip
    to get a loan number that is used to create the loan"""
    try:
        with connections[DB_ALIAS].cursor() as cursor:
            # Execute the stored procedure with output parameter
            cursor.execute(
                """
            DECLARE @Code VARCHAR(50);
            EXEC qNextCode @EntityType = %s, @Code = @Code OUTPUT;
            SELECT @Code;
        """,
                [35],
            )
            result = cursor.fetchone()
    except DatabaseError as exc:
        raise LoanNumberUnavailable("Store procedure qNextCode Failed") from exc
    loan_code = result[0] if result else None
    if not loan_code:
        raise LoanNumberUnavailable("Store procedure qNextCode returned no code")

    return loan_code


def create_loan(
    *,
    category_id: str,
    location_id: str,
    requester_name: str,
    extension: str,
    quantity: int,
    additional_info: Optional[str] = None,
) -> str:
    """create a loan on the db and sent the loan request
    and model as dict"""
    # category_id = self.get_equip_cat_id(model_id=model_id)
    category = Category.objects.using("equip").get(categoryid=category_id)
    location = Location.objects.using("equip").get(locationid=location_id)
    site_id = location.get_site_id()
    now = timezone.now()
    loan_request_code = get_loan_number()

    if loan_request_code is None:
        raise LoanCreationError
    else:
        new_request = LoanRequest(
            loanrequestid=str(uuid.uuid4()),
            loanrequestcode=loan_request_code,
            requestdate=timezone.now(),
            # modelid=model_id,
            categoryid=category,
            locationid=location_id,
            requestedfor=f"{requester_name}- ext:{extension}",
            loanrequeststatusid=LOAN_REQUEST_STATUS_ID,
            loanrequestnotes=additional_info,
            quantity=quantity,
            siteid=site_id,
            creationdate=now,
        )
        try:
            new_request.full_clean(validate_unique=False)
        except ValidationError as exc:
            raise LoanCreationError(f"Loan request validation failed: {exc}")

        with transaction.atomic(using=DB_ALIAS):
            new_request.save(using=DB_ALIAS)

        return loan_request_code


def create_loan_from_form(cleaned_data) -> list:
    # TODO for each category check available stock in library
    # selected_category =
    categories = cleaned_data.get("category")
    loan_location = cleaned_data.get("location")
    requester_name = cleaned_data.get("requester_name")
    requester_ext = cleaned_data.get("extension")
    notes = cleaned_data.get("notes")

    loan_data = []
    for device in categories:
        loan_request_no = create_loan(
            category_id=device.category_id,
            location_id=loan_location.locationid,
            requester_name=requester_name,
            extension=requester_ext,
            additional_info=notes,
            quantity=1,
        )
        loan_data.append(
            {
                "request_number": loan_request_no,
                "category": device.display_name,
            }
        )
    return loan_data
