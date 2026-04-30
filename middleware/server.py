import sys
from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from flask import Flask, redirect, request, session, url_for, jsonify
#from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
# 🔹 Automation pipeline
from automation.gmail_reader import fetch_emails_with_body
from automation.excel_writer import save_emails_to_excel
from automation.auth import get_flow, build_gmail_service
#from automation.ml.predict import ml_predict

import os
import json
import pandas as pd


app = Flask(__name__)
app.secret_key = "mailsense-secret"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Only for local dev

# -------------------------
# Homepage
# -------------------------
@app.route("/")
def index():
    return "MailSense Backend Running. Go to /login to authenticate Gmail."

# -------------------------
# Login route
# -------------------------
@app.route("/login")
def login():
    flow = get_flow()

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    # ✅ Store BOTH state and code_verifier
    session["state"] = state
    session["code_verifier"] = flow.code_verifier

    return redirect(auth_url)


# -------------------------
# OAuth callback
# -------------------------
@app.route("/oauth2callback")
def oauth2callback():
    state = session.get("state")
    code_verifier = session.get("code_verifier")

    flow = get_flow(state=state)

    # ✅ Restore PKCE verifier
    flow.code_verifier = code_verifier

    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials
    session["credentials"] = creds.to_json()

    service = build_gmail_service(creds)
    profile = service.users().getProfile(userId="me").execute()

    return f"Authenticated as {profile['emailAddress']}<br>Go to <a href='/fetch_emails'>Fetch Emails</a>"
# -------------------------
# Fetch emails route
# -------------------------

@app.route("/fetch_emails")
def fetch_emails():
    creds_json = session.get("credentials")
    if not creds_json:
        return redirect(url_for("login"))

    creds = Credentials.from_authorized_user_info(json.loads(creds_json))

    # 🔥 Auto-refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        session["credentials"] = creds.to_json()

    service = build_gmail_service(creds)

    # Get logged-in user email
    profile = service.users().getProfile(userId="me").execute()
    user_email = profile.get("emailAddress")

    # Fetch emails
    emails = fetch_emails_with_body(
        service,
        user_email=user_email,
        #max_results=30  # Limit for testing; remove or increase in production
    )

    # Save emails to user's Sheets
    save_emails_to_excel(emails, creds)

    return jsonify({
        "status": "success",
        "user": user_email,
        "emails_processed": len(emails)
    })

# -------------------------
# Run Flask server
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
