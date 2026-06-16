from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_library_request_bleep(loan_data, location_name):
    loan_items = []
    for number in loan_data:
        loan_no = number.get("request_number")
        category = number.get("category")
        loan_items.append(f"Loan ID: {loan_no} - {category}")
    message_body = "\n".join(loan_items)

    send_mail(
        subject=f"Request for {location_name}",
        message=message_body,
        from_email="mpce_app@stgeorges.nhs.uk",
        recipient_list=[
            "qurban.mohebi@stgeorges.nhs.uk",
        ],
    )
