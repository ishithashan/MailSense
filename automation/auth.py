from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from automation.config import SCOPES
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[1]

# Use env variable OR fallback (local dev only)
env_path = os.getenv("GOOGLE_CREDENTIALS")

if env_path and Path(env_path).exists():
    CREDENTIALS_PATH = env_path
else:
    CREDENTIALS_PATH = str(BASE_DIR / "credentials.json")
    
print("Using credentials at:", CREDENTIALS_PATH)
def get_flow(state=None):
    if not Path(CREDENTIALS_PATH).exists():
        raise FileNotFoundError(f"credentials.json not found at {CREDENTIALS_PATH}")

    return Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        state=state,
        redirect_uri="http://localhost:5000/oauth2callback"
    )

def build_gmail_service(credentials):
    """
    Build Gmail API service with user credentials.
    """
    service = build("gmail", "v1", credentials=credentials)
    return service

def build_sheets_service(credentials):
    """
    Build Sheets API service with user credentials.
    """
    service = build("sheets", "v4", credentials=credentials)
    return service
