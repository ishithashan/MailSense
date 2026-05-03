import sys
from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from flask import Flask, session, jsonify, render_template, redirect, request, url_for
from flask_cors import CORS
from flask_session import Session
from flask import send_from_directory

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

app = Flask(
    __name__,
    static_folder="../frontend/dist",
    static_url_path=""
)

CORS(
    app,
    supports_credentials=True,
    origins=["https://recmailsense.onrender.com"]
)
app.config["SECRET_KEY"] = "mailsense-secret"

app.config.update(
    SESSION_TYPE="filesystem",
    SESSION_PERMANENT=False,
    SESSION_USE_SIGNER=True,
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
)

Session(app)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]
if os.getenv("RENDER") is None:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Only for local dev

# -------------------------
# Login route
# -------------------------
@app.route("/api/login")
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

    response = redirect(auth_url)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

# -------------------------
# OAuth callback
# -------------------------
@app.route("/api/oauth2callback")
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
    session.modified = True # 🔥 ENSURE SESSION IS SAVED

    FRONTEND_URL = "https://recmailsense.onrender.com"
    return redirect(FRONTEND_URL + "/main")

# -------------------------
# check auth route
# -------------------------
@app.route("/api/check_auth")
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

@app.route("/api/fetch_emails")
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
# Homepage
# -------------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)

    return send_from_directory(app.static_folder, "index.html")
# -------------------------
# Run Flask server
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)