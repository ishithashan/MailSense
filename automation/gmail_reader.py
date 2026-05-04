from datetime import datetime
import base64
from automation.body_cleaner import clean_email_body
from ml.predict import classify_email
from email.utils import parseaddr
from datetime import timezone, timedelta

# -------------------------
# Base64 Decoder
# -------------------------
def _decode_base64(data):
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

# -------------------------
# Basic HTML cleaner (removing forwarded chains)
# -------------------------
def clean_html(body):
    import re

    # Remove forwarded chain
    body = re.split(r"---------- Forwarded message ---------", body, flags=re.IGNORECASE)[0]

    # Remove excessive blank lines
    body = re.sub(r'\n\s*\n', '\n', body)

    return body

# -------------------------
# Extract email body (recursive)
# -------------------------
def extract_body(payload):
    import base64

    # ✅ Prefer HTML first
    if payload.get("mimeType") == "text/html" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(
            payload["body"]["data"]
        ).decode("utf-8", errors="ignore")

    # fallback to plain text
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(
            payload["body"]["data"]
        ).decode("utf-8", errors="ignore")

    # recursive
    if "parts" in payload:
        for part in payload["parts"]:
            body = extract_body(part)
            body = clean_html(body)
            if body:
                return body

    return ""

# -------------------------
# Fetch emails (00:00 AM → login time)
# -------------------------
def fetch_emails_with_body(service, user_email):
    now = datetime.now()

    # Today at 00:00 AM (local time)
    today_str = datetime.now().strftime("%Y/%m/%d")
    query = f"after:{today_str}"

    emails = []

    # Initial request
    response = service.users().messages().list(
        userId="me",
        q=query
    ).execute()

    while True:
        messages = response.get("messages", [])

        for msg in messages:
            message = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full"
            ).execute()

            headers = message["payload"]["headers"]

            sender = next((h["value"] for h in headers if h["name"] == "From"), "")
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")

            # Read / Unread status
            status = "UNREAD" if "UNREAD" in message.get("labelIds", []) else "READ"

            # Time & Date
            internal_date = message.get("internalDate")
            time = ""
            date = ""

            if internal_date:
                IST = timezone(timedelta(hours=5, minutes=30))

                dt = datetime.fromtimestamp(
                    int(internal_date) / 1000,
                    tz=timezone.utc
                ).astimezone(IST)

                time = dt.strftime("%I:%M %p")   # 10:30 AM format
                date = dt.strftime("%d %b")

            raw_body = extract_body(message["payload"])
            body = clean_html(raw_body)

            # Step 1: Rule-based
            category = classify_by_sender(sender)

            # Step 2: If no rule matched → use SVM
            if not category:
                category = classify_email(subject, body)

            emails.append({
                "id": msg["id"],   # 🔥 ADD THIS (CRITICAL)
                "user_email": user_email,
                "sender": sender,
                "subject": subject,
                "time": time,
                "date": date,
                "body": body,
                "status": status,
                "category": category   # ✅ NEW
            })

        # Pagination handling
        if "nextPageToken" not in response:
            break

        response = service.users().messages().list(
            userId="me",
            q=query,
            pageToken=response["nextPageToken"]
        ).execute()

    return emails

# -------------------------
# Sender-based classification (backup)
# -------------------------
def get_sender_email(sender):
    name, email = parseaddr(sender)
    return email.lower()

def classify_by_sender(sender):
    email = get_sender_email(sender)

    # Placement emails
    if email in [
        "placementexecutive1@rajalakshmi.edu.in",
        "placementexecutive2@rajalakshmi.edu.in",
        "placement@rajalakshmi.edu.in"
    ]:
        return "Placement"


    # NPTEL emails
    if email in [
        "nptel@rajalakshmi.edu.in",
        "onlinecourses@nptel.iitm.ac.in"
    ]:
        return "NPTEL"

    if "@nptel.iitm.ac.in" in email:
        return "NPTEL"

    # UiPath emails
    if email in [
        "uipath@rajalakshmi.edu.in",
        "community@uipath.com"
    ]:
        return "UiPath"

    # Google Classroom
    if "no-reply@classroom.google.com" in email:
        return "GCR"

    # Google Forms
    if "forms-receipts-noreply@google.com" in email:
        return "Google Forms"

    return None  # "General"