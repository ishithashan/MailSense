import os
import json
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from automation.config import SCOPES

# Read credentials from ENV (NOT FILE)
credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

REDIRECT_URI = "https://recmailsense.onrender.com/api/oauth2callback"

def get_flow(state=None):
    if not credentials_json:
        raise ValueError("GOOGLE_CREDENTIALS_JSON not set")

    return Flow.from_client_config(
        json.loads(credentials_json),
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI
    )

def build_gmail_service(credentials):
    return build("gmail", "v1", credentials=credentials)

def build_sheets_service(credentials):
    return build("sheets", "v4", credentials=credentials)