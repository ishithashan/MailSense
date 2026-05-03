from automation.auth import build_gmail_service
from automation.gmail_reader import fetch_emails_with_body
from automation.email_writer import save_emails_to_excel

from google.oauth2.credentials import Credentials


def run_pipeline(creds_json, user_email):
    credentials = Credentials.from_authorized_user_info(creds_json)

    # Gmail service
    gmail_service = build_gmail_service(credentials)

    # 🔥 FETCH + CLASSIFY
    emails = fetch_emails_with_body(gmail_service, user_email)

    # 🔥 SAVE
    save_emails_to_excel(emails, credentials)

    return emails