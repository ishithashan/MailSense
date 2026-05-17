import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ====================== NEW GOOGLE GENAI SDK ======================
from google import genai
from google.genai.types import Part

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    print("❌ ERROR: GEMINI_API_KEY is missing in .env or Render!", file=sys.stderr)
    client = None
else:
    try:
        client = genai.Client(api_key=gemini_api_key)
        print("✅ New Google GenAI SDK initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize GenAI client: {e}", file=sys.stderr)
        client = None
# =================================================================

# Rest of your imports (keep as they are)
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
    'https://www.googleapis.com/auth/gmail.modify',        # for starring
    'https://www.googleapis.com/auth/calendar.events',
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

# ====================== STAR / IMPORTANT ======================
@app.route("/api/email/<message_id>/star", methods=["POST"])
def toggle_star(message_id):
    creds_json = session.get("credentials")
    if not creds_json:
        return jsonify({"status": "unauthorized"}), 401

    try:
        creds = Credentials.from_authorized_user_info(json.loads(creds_json))
        service = build_gmail_service(creds)

        # Toggle STAR (IMPORTANT label)
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"addLabelIds": ["STARRED"]}
        ).execute()

        return jsonify({"status": "success", "message": "Email starred"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/summarize", methods=["POST"])
def summarize():
    if not client:
        return jsonify({"status": "error", "summary": "Gemini client not initialized. Check API key."})

    data = request.get_json()
    subject = data.get("subject", "")
    body = data.get("body", "")
    category = data.get("category", "General")

    try:
        prompt = f"""
        You are an intelligent email assistant. Summarize this email concisely and professionally.

        Subject: {subject}
        Category: {category}

        Email Content:
        {body[:8000]}  # Limit length
        """

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[prompt]
        )

        summary = response.text if response.text else "Could not generate summary."
        return jsonify({"status": "success", "summary": summary})

    except Exception as e:
        print(f"Summarize error: {e}", file=sys.stderr)
        return jsonify({"status": "error", "summary": "AI service error. Please try again."})

@app.route("/api/draft_reply", methods=["POST"])
def draft_reply():
    if not client:
        return jsonify({"status": "error", "reply": "Gemini client not initialized."})

    data = request.get_json()
    subject = data.get("subject", "")
    body = data.get("body", "")
    sender = data.get("sender", "")

    try:
        prompt = f"""
        You are a professional email assistant. Draft a polite, concise and natural reply.

        Original Email From: {sender}
        Subject: {subject}

        Email Content:
        {body[:7000]}

        Write a good reply:
        """

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[prompt]
        )

        reply = response.text if response.text else "Could not draft reply."
        return jsonify({"status": "success", "reply": reply})

    except Exception as e:
        print(f"Draft reply error: {e}", file=sys.stderr)
        return jsonify({"status": "error", "reply": "AI service error. Please try again."})


# -------------------------
# Add to Calendar route
# -------------------------
@app.route("/api/add_to_calendar", methods=["POST"])
def add_to_calendar():
    creds_json = session.get("credentials")
    if not creds_json:
        return jsonify({"status": "unauthorized"}), 401

    data = request.get_json()
    summary = data.get("summary")
    description = data.get("description")
    start_time = data.get("start")   # ISO format

    try:
        creds = Credentials.from_authorized_user_info(json.loads(creds_json))
        service = build("calendar", "v3", credentials=creds)

        event = {
            'summary': summary or 'MailSense Event',
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},  # Same for now
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        return jsonify({"status": "success", "event": event})
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