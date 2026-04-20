"""
Google Calendar client using Google API + OAuth2.
Fetches calendar events for the Chief of Staff triage system.
"""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Use combined token if available (Gmail + GCal), else separate
GCAL_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
TOKEN_PATH = Path(__file__).parent / "credentials" / "gcal_token.json"
CREDS_PATH = Path(__file__).parent / "credentials" / "client_secret.json"


def get_gcal_service():
    """Authenticate and return a Google Calendar API service object."""
    creds = None
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), GCAL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_PATH.exists():
                raise FileNotFoundError(
                    f"OAuth credentials not found at {CREDS_PATH}\n"
                    "Please follow setup/oauth-setup.md to create them."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), GCAL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def fetch_todays_events(lookahead_hours: int = 48) -> list[dict]:
    """
    Fetch events for today and optionally next `lookahead_hours`.

    Returns a list of event dicts with: title, start, end, location, attendees, description.
    """
    try:
        service = get_gcal_service()
    except FileNotFoundError as e:
        print(f"[GCal] Not connected: {e}")
        return []

    now = datetime.now(timezone.utc)
    time_min = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    time_max = (now + timedelta(hours=lookahead_hours)).isoformat()

    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=20,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
    except HttpError as e:
        print(f"[GCal] API error: {e}")
        return []

    events = []
    for event in events_result.get("items", []):
        start = event.get("start", {})
        end = event.get("end", {})
        attendees = [
            a.get("email", "") for a in event.get("attendees", [])
            if not a.get("self", False)
        ]

        events.append({
            "title": event.get("summary", "(no title)"),
            "start": start.get("dateTime", start.get("date", "")),
            "end": end.get("dateTime", end.get("date", "")),
            "location": event.get("location", ""),
            "attendees": attendees,
            "description": (event.get("description", "") or "")[:300],
            "meeting_link": _extract_meeting_link(event),
        })

    return events


def _extract_meeting_link(event: dict) -> str:
    """Extract meeting link from conferenceData or location."""
    conf = event.get("conferenceData", {})
    for ep in conf.get("entryPoints", []):
        if ep.get("entryPointType") == "video":
            return ep.get("uri", "")
    loc = event.get("location", "")
    if "meet.google.com" in loc or "zoom.us" in loc:
        return loc
    return ""


def format_events_for_prompt(events: list[dict]) -> str:
    """Format calendar events into a clean string for LLM consumption."""
    if not events:
        return "No calendar events found for today/tomorrow.\n"

    lines = [f"## Calendar ({len(events)} events)\n"]
    for e in events:
        start_str = e["start"]
        # Try to format datetime nicely
        try:
            dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            start_str = dt.strftime("%a %b %d, %I:%M %p %Z")
        except Exception:
            pass

        lines.append(f"### {e['title']}")
        lines.append(f"Time: {start_str}")
        if e["location"]:
            lines.append(f"Location: {e['location']}")
        if e["meeting_link"]:
            lines.append(f"Meeting Link: {e['meeting_link']}")
        if e["attendees"]:
            lines.append(f"Attendees: {', '.join(e['attendees'][:5])}")
        if e["description"]:
            lines.append(f"Notes: {e['description'][:200]}")
        lines.append("---")

    return "\n".join(lines)
