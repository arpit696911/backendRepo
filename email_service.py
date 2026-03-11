import os
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def send_email(recipient: str, summary: str) -> None:

    if not EMAIL_USER or not EMAIL_PASS:
        raise RuntimeError(
            "EMAIL_USER and/or EMAIL_PASS not set."
        )

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))

    msg = EmailMessage()
    msg["Subject"] = "Sales Insight Automator - Analysis Summary"
    msg["From"] = EMAIL_USER
    msg["To"] = recipient
    msg.set_content(summary)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)