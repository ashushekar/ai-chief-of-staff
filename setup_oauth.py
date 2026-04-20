"""
OAuth Setup Script for Gmail + Google Calendar.
Run this ONCE after placing client_secret.json in credentials/.

Usage:
    c:\Study\pbkyc\.venv\Scripts\python.exe setup_oauth.py

This opens a browser window, you sign in, then tokens are saved
to credentials/gmail_token.json and credentials/gcal_token.json.
All future triage runs use the saved tokens — no more browser prompts.
"""

import sys
from pathlib import Path

CREDS_DIR = Path(__file__).parent / "credentials"
CLIENT_SECRET = CREDS_DIR / "client_secret.json"
GMAIL_TOKEN   = CREDS_DIR / "gmail_token.json"
GCAL_TOKEN    = CREDS_DIR / "gcal_token.json"

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
GCAL_SCOPES  = ["https://www.googleapis.com/auth/calendar.readonly"]


def check_prereqs():
    if not CLIENT_SECRET.exists():
        print("\n[ERROR] client_secret.json not found.")
        print(f"Expected at: {CLIENT_SECRET}")
        print("\nTo get it:")
        print("  1. Go to https://console.cloud.google.com/apis/credentials")
        print("     (Project: gen-lang-client-0978668617)")
        print("  2. Create credentials > OAuth client ID > Desktop app")
        print("  3. Download JSON > rename to client_secret.json")
        print(f"  4. Copy to: {CREDS_DIR}")
        return False
    return True


def authorize_gmail():
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.oauth2.credentials import Credentials

    print("\n[1/2] Authorizing Gmail (read-only)...")
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), GMAIL_SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    GMAIL_TOKEN.write_text(creds.to_json(), encoding="utf-8")
    print(f"     Gmail token saved to: {GMAIL_TOKEN}")
    return creds


def authorize_gcal():
    from google_auth_oauthlib.flow import InstalledAppFlow

    print("\n[2/2] Authorizing Google Calendar (read-only)...")
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), GCAL_SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    GCAL_TOKEN.write_text(creds.to_json(), encoding="utf-8")
    print(f"     Calendar token saved to: {GCAL_TOKEN}")
    return creds


def test_connections():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials

    print("\n[Testing connections...]")

    # Test Gmail
    try:
        gmail_creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN), GMAIL_SCOPES)
        service = build("gmail", "v1", credentials=gmail_creds)
        profile = service.users().getProfile(userId="me").execute()
        print(f"  Gmail  OK — connected as: {profile.get('emailAddress')}")
        print(f"         Total messages: {profile.get('messagesTotal', 'unknown'):,}")
    except Exception as e:
        print(f"  Gmail  FAIL: {e}")

    # Test Calendar
    try:
        from googleapiclient.discovery import build
        gcal_creds = Credentials.from_authorized_user_file(str(GCAL_TOKEN), GCAL_SCOPES)
        service = build("calendar", "v3", credentials=gcal_creds)
        cal_list = service.calendarList().list().execute()
        calendars = cal_list.get("items", [])
        primary = next((c for c in calendars if c.get("primary")), None)
        cal_name = primary.get("summary", "Primary") if primary else "unknown"
        print(f"  Calendar OK — primary calendar: {cal_name}")
        print(f"         {len(calendars)} calendars accessible")
    except Exception as e:
        print(f"  Calendar FAIL: {e}")


def main():
    print("=" * 55)
    print("  AI Chief of Staff — Gmail + Calendar OAuth Setup")
    print("=" * 55)

    if not check_prereqs():
        sys.exit(1)

    print("\nThis will open a browser window twice (once for Gmail,")
    print("once for Calendar). Sign in with your Google account")
    print("and click Allow for each.\n")
    input("Press Enter to start...")

    try:
        authorize_gmail()
        authorize_gcal()
        test_connections()

        print("\n" + "=" * 55)
        print("  Setup complete! You can now run live triage:")
        print()
        print("  $env:PYTHONIOENCODING = 'utf-8'")
        print("  c:\\Study\\pbkyc\\.venv\\Scripts\\python.exe main.py triage")
        print("=" * 55)

    except KeyboardInterrupt:
        print("\nSetup cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("\nTry again, or check setup/oauth-setup.md for troubleshooting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
