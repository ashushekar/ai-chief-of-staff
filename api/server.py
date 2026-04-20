"""
FastAPI backend for AI Chief of Staff web app.
Wraps the existing Python engine with REST + SSE streaming endpoints.

Run with:
    uvicorn api.server:app --reload --port 8000
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from chief_of_staff import (
    run_triage,
    draft_email_reply,
    chat_with_chief_of_staff,
    append_to_weekly_log,
    _load_context,
)

app = FastAPI(title="AI Chief of Staff API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request / Response Models ────────────────────────────────────────────────

class TriageRequest(BaseModel):
    demo: bool = False

class ReplyRequest(BaseModel):
    email_content: str
    intent: str = ""

class ChatRequest(BaseModel):
    message: str
    history: list = []
    triage_context: str = ""

class ContextUpdateRequest(BaseModel):
    file: str  # my-priorities | my-team | communication-style
    content: str

# ─── Helper: Demo Data ────────────────────────────────────────────────────────

def _demo_emails() -> str:
    return """## Emails (5 total)

### Email 1 [UNREAD, IMPORTANT]
From: sarah.chen@company.com (Sarah Chen, VP Product)
Subject: Orion v2 — decision needed on launch scope
Date: Today 09:15
Body: Need a final call on cutting advanced filtering or delaying v2 by 2 weeks.
Engineering says it adds 10 days. Hartwell Group demo on May 5. Your recommendation?

---

### Email 2 [UNREAD]
From: james.okafor@hartwellgroup.com (James Okafor, Hartwell Group)
Subject: Integration questions before May 5 demo
Date: Today 08:30
Body: Three integration questions our CTO wants answered before the demo.
Can we schedule a technical call this week? Competitor demo on Thursday.

---

### Email 3 [UNREAD]
From: kai.oduya@company.com (Kai Oduya, Senior PM)
Subject: QA blocker — ticket #841 needs your call
Date: Today 07:45
Body: Critical bug in data sync (#841) blocked on product decision: patch or rewrite?
Engineering needs answer today to stay on track.

---

### Email 4
From: newsletter@productops.io
Subject: 10 frameworks for product roadmap planning
Date: Yesterday

### Email 5
From: recruiter@talent.co
Subject: Exciting PM opportunity at [Top Startup]
Date: Yesterday"""


def _demo_events() -> str:
    today = datetime.now().strftime("%a %b %d")
    return f"""## Calendar (3 events)

### Standup — Engineering
Time: {today}, 09:30 AM
Notes: Daily sync. Orion v2 status, #841 blocker.

### 1:1 with Sarah Chen
Time: {today}, 11:00 AM
Notes: Weekly 1:1. Agenda: Orion v2 scope, Hartwell update.

### AI Roadmap Working Session
Time: {today}, 03:00 PM
Notes: Board presentation prep. Use cases + ROI estimates."""


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    gmail_token = (Path(__file__).parent.parent / "credentials" / "gmail_token.json").exists()
    gcal_token = (Path(__file__).parent.parent / "credentials" / "gcal_token.json").exists()
    return {
        "status": "ok",
        "gemini_configured": bool(api_key),
        "gmail_connected": gmail_token,
        "gcal_connected": gcal_token,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/triage")
async def triage(req: TriageRequest):
    """Run morning triage and return structured result."""
    try:
        if req.demo:
            emails_text = _demo_emails()
            events_text = _demo_events()
        else:
            try:
                from gmail_client import fetch_recent_emails, format_emails_for_prompt
                emails = fetch_recent_emails(hours=24)
                emails_text = format_emails_for_prompt(emails)
            except Exception as e:
                emails_text = f"Could not fetch Gmail: {e}"

            try:
                from gcal_client import fetch_todays_events, format_events_for_prompt
                events = fetch_todays_events(lookahead_hours=48)
                events_text = format_events_for_prompt(events)
            except Exception as e:
                events_text = f"Could not fetch Calendar: {e}"

        result = run_triage(emails_text, events_text)
        log_path = append_to_weekly_log(result)

        return {
            "brief": result,
            "logged_to": str(log_path),
            "timestamp": datetime.now().isoformat(),
            "demo": req.demo,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reply")
async def reply(req: ReplyRequest):
    """Draft an email reply."""
    try:
        draft = draft_email_reply(req.email_content, req.intent)
        return {"draft": draft, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Single-turn chat with history."""
    try:
        response, updated_history = chat_with_chief_of_staff(
            req.history, req.message, triage_context=req.triage_context
        )
        return {
            "response": response,
            "history": updated_history,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/context")
async def get_context():
    """Return all three context files."""
    ctx = _load_context()
    return ctx


@app.put("/api/context")
async def update_context(req: ContextUpdateRequest):
    """Update a context file."""
    valid = ["my-priorities", "my-team", "communication-style"]
    if req.file not in valid:
        raise HTTPException(status_code=400, detail=f"file must be one of {valid}")

    ctx_path = Path(__file__).parent.parent / "context" / f"{req.file}.md"
    ctx_path.write_text(req.content, encoding="utf-8")
    return {"saved": True, "file": req.file}


@app.get("/api/logs")
async def get_logs():
    """Return the contents of weekly-log.md."""
    log_path = Path(__file__).parent.parent / "logs" / "weekly-log.md"
    if not log_path.exists():
        return {"content": "", "exists": False}
    return {"content": log_path.read_text(encoding="utf-8"), "exists": True}


@app.post("/api/logs/analyze")
async def analyze_logs():
    """Analyze the weekly log with Gemini."""
    log_path = Path(__file__).parent.parent / "logs" / "weekly-log.md"
    if not log_path.exists():
        raise HTTPException(status_code=404, detail="No logs yet. Run triage first.")

    content = log_path.read_text(encoding="utf-8")
    prompt = f"""Here is my triage log:

{content}

Analyse:
1. What patterns do you see in where I'm spending time?
2. Where am I spending time that doesn't match my stated priorities?
3. What themes are recurring in my P0/P1 emails?
4. One specific recommendation to improve focus on priorities.

Be direct and specific."""

    response, _ = chat_with_chief_of_staff([], prompt)
    return {"analysis": response, "timestamp": datetime.now().isoformat()}
