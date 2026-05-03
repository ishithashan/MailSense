import sys
from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from flask import Flask, session, jsonify, render_template, redirect, request, url_for
from flask_cors import CORS #ADDED

#from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
# Automation pipeline
from automation.gmail_reader import fetch_emails_with_body
from automation.excel_writer import save_emails_to_excel
from automation.auth import get_flow, build_gmail_service
#from automation.ml.predict import ml_predict

import os
import json
import pandas as pd

app = Flask(__name__, template_folder="../frontend")
CORS(app, supports_credentials=True, origins=[
    "https://recmailsense-1.onrender.com"
])
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True
app.secret_key = "mailsense-secret"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]
if os.getenv("RENDER") is None:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Only for local dev

# -------------------------
# Homepage
# -------------------------
@app.route("/") #"/" this root, 
def index():
    FRONTEND_URL = "https://recmailsense-1.onrender.com"
    return redirect(FRONTEND_URL)

# -------------------------
# Login route
# -------------------------
@app.route("/login")
def login():
    session.clear()  # 🔥 FORCE RESET
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
    if "state" not in session or "code_verifier" not in session:
        return redirect(url_for("login"))  # 🔥 FIX

    state = session.get("state")
    code_verifier = session.get("code_verifier")

    flow = get_flow(state=state)
    flow.code_verifier = code_verifier

    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials
    session["credentials"] = creds.to_json()

    service = build_gmail_service(creds)
    profile = service.users().getProfile(userId="me").execute()

    session["user_email"] = profile["emailAddress"]

    FRONTEND_URL = os.getenv("FRONTEND_URL", "https://recmailsense-1.onrender.com")
    return redirect(FRONTEND_URL + "/main")

# -------------------------
# check auth route
# -------------------------
@app.route("/check_auth")
def check_auth():
    if "credentials" in session:
         return jsonify({
            "authenticated": True,
            "user": session.get("user_email")
        })

    return jsonify({"authenticated": False}), 401


# -------------------------
# Fetch emails route
# -------------------------

@app.route("/fetch_emails")
def fetch_emails():
    creds_json = session.get("credentials")
    # if not creds_json:
    #     return redirect(url_for("login"))
    if not creds_json:
          return jsonify({"status": "unauthorized"}), 401

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

    #return jsonify({
        #"status": "success",
        #"user": user_email,
        #"emails_processed": len(emails)
    #})
    return jsonify({
    "status": "success",
    "user": user_email,
    "emails_processed": len(emails),
    "emails": emails   # 🔥 ADD THIS LINE
    })

# -------------------------
# Run Flask server
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)