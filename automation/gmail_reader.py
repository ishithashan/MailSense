from datetime import datetime
import base64
from automation.body_cleaner import clean_email_body
from ml.predict import classify_email
from email.utils import parseaddr

# -------------------------
# Base64 Decoder
# -------------------------
def _decode_base64(data):
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")


# -------------------------
# Extract email body (recursive)
# -------------------------
def extract_body(payload):
    if payload.get("body", {}).get("data"):
        return _decode_base64(payload["body"]["data"])

    if "parts" in payload:
        for part in payload["parts"]:
            body = extract_body(part)
            if body:
                return body

    return ""


# -------------------------
# Fetch emails (00:00 AM → login time)
# -------------------------
def fetch_emails_with_body(service, user_email):
    now = datetime.now()

    # Today at 00:00 AM (local time)
    today_midnight = datetime.combine(now.date(), datetime.min.time())

    # Convert to UNIX timestamps (seconds)
    after_ts = int(today_midnight.timestamp())
    before_ts = int(now.timestamp())

    # Gmail search query
    query = f"after:{after_ts} before:{before_ts}"

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
                dt = datetime.fromtimestamp(int(internal_date) / 1000)
                time = dt.strftime("%H:%M")
                date = dt.strftime("%d %b")

            raw_body = extract_body(message["payload"])
            body = clean_email_body(raw_body)

            # Step 1: Rule-based
            category = classify_by_sender(sender)

            # Step 2: If no rule matched → use SVM
            if not category:
                category = classify_email(subject, body)

            emails.append({
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