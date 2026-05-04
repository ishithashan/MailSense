from automation.auth import build_sheets_service

def read_emails_from_sheet(credentials, spreadsheet_id):
    service = build_sheets_service(credentials)

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="Sheet1!A2:H"
    ).execute()

    rows = result.get("values", [])

    emails = []
    for row in rows:
        emails.append({
            "id": row[0],          # ✅ NEW
            "user_email": row[1],
            "sender": row[2],
            "subject": row[3],
            "time": row[4],
            "date": row[5],
            "body": row[6],
            "status": row[7],
            "category": row[8]
        })

    return emails