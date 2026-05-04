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
            "user_email": row[0],
            "sender": row[1],
            "subject": row[2],
            "time": row[3],
            "date": row[4],
            "body": row[5],
            "status": row[6],
            "category": row[7]
        })

    return emails