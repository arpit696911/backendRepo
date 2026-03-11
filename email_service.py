import os
import resend

resend.api_key = os.getenv("RESEND_API_KEY")

def send_email(recipient: str, summary: str) -> None:
    """
    Send the AI-generated summary using the Resend email API.
    """
    if not resend.api_key:
        raise RuntimeError("RESEND_API_KEY not set in environment variables")

    resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": [recipient],
        "subject": "Sales Insight Automator - Analysis Summary",
        "html": f"<pre>{summary}</pre>"
    })
