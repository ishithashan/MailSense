import os
import sys
#from pathlib import Path

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai

# === Gemini Configuration ===
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    print("❌ ERROR: GEMINI_API_KEY not found in .env!", file=sys.stderr)
    gemini_model = None
else:
    try:
        genai.configure(api_key=gemini_api_key)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        print("✅ Gemini 1.5 Flash model loaded successfully")
    except Exception as e:
        print(f"❌ Gemini initialization failed: {e}", file=sys.stderr)
        gemini_model = None
    
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
from automation.gmail_reader import clean_html
from automation.excel_writer import save_emails_to_excel
from automation.auth import get_flow, build_gmail_service
from automation.pipeline import run_pipeline

#from automation.ml.predict import ml_predict

import os
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "frontend" / "dist"

print("STATIC DIR:", STATIC_DIR)
print("EXISTS:", STATIC_DIR.exists())

app = Flask(
    __name__,
    static_folder=str(STATIC_DIR),
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
    return redirect(FRONTEND_URL + "/")

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

    if not creds_json:
        return jsonify({"status": "unauthorized"}), 401

    try:
        user_email = session.get("user_email")

        if not user_email:
            return jsonify({"status": "error", "message": "User email not found"}), 400

        # 🔥 RUN FULL PIPELINE
        # First update Excel
        run_pipeline(creds_json, user_email)

        # Then READ from Excel
        from automation.excel_reader import read_emails_from_sheet
        from automation.excel_writer import get_or_create_sheet

        creds = Credentials.from_authorized_user_info(json.loads(creds_json))
        spreadsheet_id = get_or_create_sheet(creds)

        emails = read_emails_from_sheet(creds, spreadsheet_id)

        return jsonify({
            "status": "success",
            "user": user_email,
            "emails": emails,
            "count": len(emails)
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# -------------------------
# Get single email body
# -------------------------
@app.route("/api/email/<message_id>")
def get_single_email(message_id):
    creds_json = session.get("credentials")

    if not creds_json:
        return jsonify({"status": "unauthorized"}), 401

    creds = Credentials.from_authorized_user_info(json.loads(creds_json))

    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        session["credentials"] = creds.to_json()

    service = build_gmail_service(creds)

    try:
        message = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full"
        ).execute()

        # Extract body
        def extract_body(payload):
            if payload.get("body", {}).get("data"):
                import base64
                return base64.urlsafe_b64decode(
                    payload["body"]["data"]
                ).decode("utf-8", errors="ignore")

            if "parts" in payload:
                for part in payload["parts"]:
                    body = extract_body(part)
                    if body:
                        return body
            return ""

        raw_body = extract_body(message["payload"])
        body = clean_html(raw_body)   # ✅ APPLY CLEANING HERE

        return jsonify({
            "status": "success",
            "body": body
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ─────────────────────────────────────────────────────────────────
# AI Email Summary route
# ─────────────────────────────────────────────────────────────────
@app.route("/api/summarize", methods=["POST"])
def summarize_email():
    if "credentials" not in session:
        return jsonify({"status": "unauthorized"}), 401

    data = request.get_json()
    subject  = data.get("subject", "")
    body     = data.get("body", "")
    category = data.get("category", "General")

    if not body and not subject:
        return jsonify({"status": "error", "message": "No content to summarize"}), 400

    # Truncate body so it fits easily in the prompt
    truncated_body = body[:4000] if len(body) > 4000 else body

    prompt = f"""You are a smart email assistant for a student.
Summarize this email in 3-4 concise bullet points (plain text, no markdown symbols).
Focus on: what the email is about, any deadlines or action items, and why it matters.
Keep it short and clear — the student should understand in 5 seconds.

Email Category: {category}
Subject: {subject}
Body:
{truncated_body}

Return ONLY the bullet points, each on its own line starting with •"""

    try:
        response = gemini_model.generate_content(prompt)
        summary = response.text.strip()
        return jsonify({"status": "success", "summary": summary})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ─────────────────────────────────────────────────────────────────
# AI Reply Draft route
# ─────────────────────────────────────────────────────────────────
@app.route("/api/draft_reply", methods=["POST"])
def draft_reply():
    if "credentials" not in session:
        return jsonify({"status": "unauthorized"}), 401

    data = request.get_json()
    subject  = data.get("subject", "")
    body     = data.get("body", "")
    sender   = data.get("sender", "")
    category = data.get("category", "General")

    truncated_body = body[:3000] if len(body) > 3000 else body

    prompt = f"""You are a helpful email assistant for a student.
Draft a polite, professional, and concise reply to this email.
The reply should be appropriate for a student replying to their college or institution.
Keep it short (3-5 sentences max). Do NOT include a subject line.
Start with a proper greeting and end with a sign-off.

Email Category: {category}
From: {sender}
Subject: {subject}
Email body:
{truncated_body}

Write only the reply text, nothing else."""

    try:
        response = gemini_model.generate_content(prompt)
        reply = response.text.strip()
        return jsonify({"status": "success", "reply": reply})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500   

# -------------------------
# Homepage
# -------------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    full_path = os.path.join(app.static_folder, path)

    # If file exists → serve it
    if path != "" and os.path.exists(full_path):
        return send_from_directory(app.static_folder, path)

    # Otherwise ALWAYS return React app
    return send_from_directory(app.static_folder, "index.html")

# -------------------------
# Run Flask server
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)