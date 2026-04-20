"""
Gmail client using Google API + OAuth2.
Fetches emails for the Chief of Staff triage system.
"""

import os
import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scopes: read-only Gmail access
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_PATH = Path(__file__).parent / "credentials" / "gmail_token.json"
CREDS_PATH = Path(__file__).parent / "credentials" / "client_secret.json"


def get_gmail_service():
    """Authenticate and return a Gmail API service object."""
    creds = None
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_PATH.exists():
                raise FileNotFoundError(
                    f"OAuth credentials not found at {CREDS_PATH}\n"
                    "Please follow setup/oauth-setup.md to create them."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _decode_body(part):
    """Decode email body from base64."""
    data = part.get("body", {}).get("data", "")
    if data:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    return ""


def _extract_text(payload):
    """Recursively extract plain text from email payload."""
    mime_type = payload.get("mimeType", "")
    parts = payload.get("parts", [])

    if mime_type == "text/plain":
        return _decode_body(payload)
    if mime_type == "text/html" and not parts:
        # Fallback: return raw html snippet (truncated)
        return _decode_body(payload)[:500]
    for part in parts:
        text = _extract_text(part)
        if text.strip():
            return text
    return ""


def fetch_recent_emails(hours: int = 24, max_results: int = 50) -> list[dict]:
    """
    Fetch emails from the last `hours` hours.

    Returns a list of dicts with: id, from, to, subject, date, snippet, body (truncated).
    """
    try:
        service = get_gmail_service()
    except FileNotFoundError as e:
        print(f"[Gmail] Not connected: {e}")
        return []

    # Calculate the time threshold
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    since_ts = int(since.timestamp())

    try:
        response = service.users().messages().list(
            userId="me",
            q=f"after:{since_ts}",
            maxResults=max_results,
        ).execute()
    except HttpError as e:
        print(f"[Gmail] API error: {e}")
        return []

    messages = response.get("messages", [])
    emails = []

    for msg_ref in messages:
        try:
            msg = service.users().messages().get(
                userId="me",
                id=msg_ref["id"],
                format="full",
            ).execute()

            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            body = _extract_text(msg["payload"])
            # Truncate body to 800 chars for LLM context efficiency
            body_preview = body.strip()[:800] if body else msg.get("snippet", "")

            emails.append({
                "id": msg["id"],
                "from": headers.get("From", "Unknown"),
                "to": headers.get("To", ""),
                "subject": headers.get("Subject", "(no subject)"),
                "date": headers.get("Date", ""),
                "labels": msg.get("labelIds", []),
                "snippet": msg.get("snippet", ""),
                "body": body_preview,
                "is_unread": "UNREAD" in msg.get("labelIds", []),
                "is_important": "IMPORTANT" in msg.get("labelIds", []),
            })
        except HttpError:
            continue

    return emails


def format_emails_for_prompt(emails: list[dict]) -> str:
    """Format email list into a clean string for LLM consumption."""
    if not emails:
        return "No emails found in the last 24 hours.\n"

    lines = [f"## Emails ({len(emails)} total)\n"]
    for i, e in enumerate(emails, 1):
        flags = []
        if e.get("is_unread"):
            flags.append("UNREAD")
        if e.get("is_important"):
            flags.append("IMPORTANT")
        flag_str = f" [{', '.join(flags)}]" if flags else ""

        lines.append(f"### Email {i}{flag_str}")
        lines.append(f"From: {e['from']}")
        lines.append(f"Subject: {e['subject']}")
        lines.append(f"Date: {e['date']}")
        lines.append(f"Body preview:\n{e['body'][:600]}")
        lines.append("---")

    return "\n".join(lines)
