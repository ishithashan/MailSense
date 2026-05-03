from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from automation.config import SCOPES
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[1]

# Use env variable OR fallback
env_path = os.getenv("GOOGLE_CREDENTIALS")

if env_path and Path(env_path).exists():
    CREDENTIALS_PATH = env_path
else:
    CREDENTIALS_PATH = str(BASE_DIR / "credentials.json")

print("Using credentials at:", CREDENTIALS_PATH)

# 🔥 ADD THIS
REDIRECT_URI = os.getenv(
    "REDIRECT_URI",
    "https://recmailsense.onrender.com/oauth2callback" # default for production
)

def get_flow(state=None):
    if not Path(CREDENTIALS_PATH).exists():
        raise FileNotFoundError(f"credentials.json not found at {CREDENTIALS_PATH}")

    return Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI   # 🔥 USE VARIABLE
    )

def build_gmail_service(credentials):
    return build("gmail", "v1", credentials=credentials)

def build_sheets_service(credentials):
    return build("sheets", "v4", credentials=credentials)