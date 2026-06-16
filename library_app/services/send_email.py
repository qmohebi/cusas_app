import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from environs import Env

env = Env()
env.read_env()

SMTP = env("SMTP")
PORT = env("SMTP_PORT")


class SendEmail:
    """Send email using pythong SMTP library, by providing the
    necessary information. SMTP details are in the config.json file."""

    def __init__(self) -> None:
        self.smtp_server = SMTP
        self.smtp_port = PORT

    def send_email(
        self, sender: str, receiver: str, subject: str, body: str, copy: str = None
    ):

        self.sender = sender
        self.receiver = receiver
        self.copy = copy
        self.body = body
        self.subject = subject

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                msg = MIMEMultipart("Alternative")
                content = MIMEText(self.body, "html")
                msg["From"] = sender
                msg["To"] = receiver
                msg["Cc"] = copy
                msg["Subject"] = self.subject
                msg.attach(content)
                server.sendmail(self.sender, self.receiver, msg.as_string())
        except Exception as e:
            logging.debug(e)


if __name__ == "__main__":
    email = SendEmail()
    body = "45 - CTICU - Cardio-Thoracic Intensive Care - Infusion Pump"
    email.send_email(
        "librar_app@stgeorges.nhs.uk",
        receiver="6183@isearch.net.stgeorges.nhs.uk",
        subject="App Request",
        body=body,
    )
