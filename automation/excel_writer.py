from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from automation.auth import build_sheets_service

SHEET_TITLE = "RECMailSense_Emails"
HEADERS = ["id", "user_email", "sender", "subject", "time", "date", "body", "status", "category"]

def get_or_create_sheet(credentials):
    """
    Open the user's RECMailSense_Emails sheet if it exists, else create a new one.
    Returns the spreadsheet ID.
    """
    service = build_sheets_service(credentials)
    
    # Check if spreadsheet exists (search by name)
    try:
        drive_service = build("drive", "v3", credentials=credentials)
        results = drive_service.files().list(
            q=f"name='{SHEET_TITLE}' and mimeType='application/vnd.google-apps.spreadsheet'",
            spaces='drive',
            fields="files(id, name)"
        ).execute()
        files = results.get("files", [])

        if files:
            # Spreadsheet exists
            spreadsheet_id = files[0]['id']
        else:
            # Create spreadsheet
            spreadsheet = {
                'properties': {'title': SHEET_TITLE},
                'sheets': [{'properties': {'title': 'Sheet1'}}]
            }
            spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')

            # Add headers
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A1',
                valueInputOption='RAW',
                body={'values': [HEADERS]}
            ).execute()
    except HttpError as err:
        print("Error accessing Sheets:", err)
        raise err

    return spreadsheet_id

"""
def save_emails_to_excel(emails, credentials):
    #Save emails to the user's spreadsheet in their Drive.
    service = build_sheets_service(credentials)
    spreadsheet_id = get_or_create_sheet(credentials)

    # Prepare rows to append
    rows = []
    for email in emails:
        rows.append([
            email.get("user_email", ""),
            email.get("sender", ""),
            email.get("subject", ""),
            email.get("time", ""),
            email.get("date", ""),
            email.get("body", ""),
            email.get("status", ""),
            email.get("category", "")   # ✅ ADD THIS
        ])

    # Append rows at the end of sheet
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range='Sheet1',
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': rows}
    ).execute()

    print("Spreadsheet ID:", spreadsheet_id)
    print("Open URL: https://docs.google.com/spreadsheets/d/" + spreadsheet_id)
"""
def save_emails_to_excel(emails, credentials):
    """
    Clear previous data and write fresh emails.
    """
    service = build_sheets_service(credentials)
    spreadsheet_id = get_or_create_sheet(credentials)

    if not emails:
        print("No emails to save.")
        return

    # Prepare rows
    rows = []
    for email in emails:
        rows.append([
            email.get("id", ""),   # ✅ ADD THIS
            email.get("user_email", ""),
            email.get("sender", ""),
            email.get("subject", ""),
            email.get("time", ""),
            email.get("date", ""),
            email.get("body", ""),
            email.get("status", ""),
            email.get("category", "")
        ])

    try:
        # 🔥 STEP 1: Clear old data (keep header)
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A2:Z'
        ).execute()

        # 🔥 STEP 2: Write new data from row 2
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A2',
            valueInputOption='RAW',
            body={'values': rows}
        ).execute()

        print(f"✅ Sheet updated with {len(rows)} emails")
        print("Open URL: https://docs.google.com/spreadsheets/d/" + spreadsheet_id)

    except HttpError as err:
        print("Error updating sheet:", err)
        raise err