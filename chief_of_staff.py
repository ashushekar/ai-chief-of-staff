"""
Gemini-powered Chief of Staff engine.
Orchestrates context loading, email/calendar data, and LLM calls.
"""

import os
from pathlib import Path
from datetime import datetime
from google import genai
from google.genai import types

CONTEXT_DIR = Path(__file__).parent / "context"
SKILLS_DIR = Path(__file__).parent / "skills"
LOGS_DIR = Path(__file__).parent / "logs"

# Gemini models — update these if newer models become available
# Gemini models — update these if newer models become available
TRIAGE_MODEL = os.environ.get("TRIAGE_MODEL", "gemini-2.5-flash")  # fast & smart for daily triage
REPLY_MODEL = os.environ.get("REPLY_MODEL", "gemini-2.5-pro")       # highest quality for drafts


def _load_context() -> dict[str, str]:
    """Load all three context files."""
    ctx = {}
    for fname in ["my-priorities.md", "my-team.md", "communication-style.md"]:
        fpath = CONTEXT_DIR / fname
        if fpath.exists():
            ctx[fname] = fpath.read_text(encoding="utf-8")
        else:
            ctx[fname] = f"[{fname} not found — please create it in the context/ directory]"
    return ctx


def _load_skill(skill_name: str) -> str:
    """Load a skill definition file."""
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return ""


def _get_client() -> genai.Client:
    """
    Create and return a Gemini client.

    Auth modes (tried in order):
    1. GEMINI_API_KEY or GOOGLE_API_KEY env var → AI Studio (recommended)
    2. Vertex AI with vertexai=True + PROJECT_ID + LOCATION (standard GCP project)
    3. Vertex AI using gcloud access token as API key workaround (personal ADC)
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key)

    # Try Vertex AI — requires a real GCP project (not gen-lang-client-*)
    project_id = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("LOCATION", "us-central1")

    if project_id and not project_id.startswith("gen-lang-client"):
        # Standard GCP project — use Vertex AI endpoint
        return genai.Client(vertexai=True, project=project_id, location=location)

    # Fallback: try getting a gcloud access token and use it as the API key
    # This works when the user has run: gcloud auth login + gcloud auth application-default login
    token = _get_gcloud_token()
    if token:
        # Use AI Studio endpoint with OAuth token as API key
        # The google-genai SDK accepts OAuth tokens via http_options override
        import google.auth
        import google.auth.transport.requests
        try:
            scopes = ["https://www.googleapis.com/auth/generative-language"]
            creds, _ = google.auth.default(scopes=scopes)
            creds.refresh(google.auth.transport.requests.Request())
            # Build client using credentials directly
            # Workaround: set GOOGLE_API_KEY to the access token temporarily
            os.environ["GOOGLE_API_KEY"] = creds.token
            client = genai.Client(api_key=creds.token)
            return client
        except Exception:
            pass

    raise ValueError(
        "No Gemini credentials found.\n\n"
        "QUICKEST FIX — Get a free API key from AI Studio:\n"
        "  1. Visit: https://aistudio.google.com/app/apikey\n"
        "  2. Create key for project 'gen-lang-client-0978668617'\n"
        "  3. Add to .env: GEMINI_API_KEY=AIza...\n\n"
        "OR — Use an existing API key:\n"
        "  $env:GEMINI_API_KEY = 'your-key-here'\n\n"
        "OR — Vertex AI with a real GCP project:\n"
        "  Set PROJECT_ID to a GCP project (not gen-lang-client-*).\n"
    )


def _get_gcloud_token() -> str:
    """Try to get a gcloud access token. Returns empty string on failure."""
    import subprocess
    gcloud_paths = [
        "gcloud",
        r"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
        r"C:\Program Files\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
    ]
    for gcloud in gcloud_paths:
        try:
            result = subprocess.run(
                [gcloud, "auth", "print-access-token"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return ""


def run_triage(emails_text: str, events_text: str) -> str:
    """
    Run the full triage command using Gemini.
    Reads context, feeds emails + calendar, returns structured brief.
    """
    client = _get_client()
    ctx = _load_context()
    today = datetime.now().strftime("%A, %B %d %Y")

    system_prompt = f"""You are an expert Chief of Staff AI assistant. Your job is to help your principal manage their time and communications with precision.

You have been given three context files that define who your principal is, what they care about, and how they communicate. Read them carefully before making ANY prioritization decisions.

=== CONTEXT: MY PRIORITIES ===
{ctx['my-priorities.md']}

=== CONTEXT: MY TEAM & STAKEHOLDERS ===
{ctx['my-team.md']}

=== CONTEXT: MY COMMUNICATION STYLE ===
{ctx['communication-style.md']}

Today is {today}.

Your triage output must use EXACTLY this structure:

---
### Morning Triage — {today}

**P0 — Act Now** (needs same-day response or action)
- [Sender] | [Subject] | [1-line summary] | Suggested action: [reply / call / decision]

**P1 — Act Today** (important, can be batched to a focused block)
- [Sender] | [Subject] | [1-line summary]

**P2 — On My Radar** (worth knowing, no immediate action)
- [Sender] | [Subject] | [1-line summary]

**Archived** (subjects only, no detail)
- [Subject], [Subject], ...

---

**Today's Calendar**
- [HH:MM] [Event title] — [1-line context or prep note if relevant]

---

**Chief of Staff Note** (1 line max, optional — flag a pattern, conflict, or something they haven't asked about)

---

After the brief, ask: "Which of these do you want to act on first?"
"""

    user_message = f"""Please run my morning triage.

{emails_text}

{events_text}

Apply my context files strictly. An email from a P0 stakeholder about a P0 topic is always P0. Filter out noise ruthlessly.
"""

    response = client.models.generate_content(
        model=TRIAGE_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            max_output_tokens=2048,
        ),
        contents=user_message,
    )

    return response.text


def draft_email_reply(email_content: str, intent: str = "") -> str:
    """
    Draft an email reply using the email-reply skill.
    """
    client = _get_client()
    ctx = _load_context()
    skill = _load_skill("email-reply")

    today = datetime.now().strftime("%A, %B %d %Y")

    system_prompt = f"""You are drafting an email reply on behalf of your principal. You must sound like them, not like a generic AI assistant.

=== MY COMMUNICATION STYLE ===
{ctx['communication-style.md']}

=== MY TEAM & STAKEHOLDERS ===
{ctx['my-team.md']}

=== EMAIL REPLY SKILL ===
{skill}

Today is {today}.

CRITICAL RULES:
- Read communication-style.md before writing a single word
- Check my-team.md to understand the sender relationship
- Never use banned phrases from communication-style.md
- Keep under 150 words unless complexity requires more
- Present draft in a clearly labeled block
- End with: "Want me to adjust tone, length, or change the ask?"
- Do NOT explain what you did or why before the draft
"""

    user_message = f"""Draft a reply to this email:

{email_content}
"""
    if intent:
        user_message += f"\nMy intent for this reply: {intent}"

    response = client.models.generate_content(
        model=REPLY_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.4,
            max_output_tokens=1024,
        ),
        contents=user_message,
    )

    return response.text


def chat_with_chief_of_staff(conversation_history: list, new_message: str, triage_context: str = "") -> tuple[str, list]:
    """
    Multi-turn conversation with the Chief of Staff.
    Returns (response_text, updated_history).
    """
    client = _get_client()
    ctx = _load_context()
    today = datetime.now().strftime("%A, %B %d %Y")

    system_prompt = f"""You are an expert Chief of Staff AI assistant powered by Gemini. 

You help your principal manage their communications, prepare for meetings, draft replies, and think through decisions. You are direct, insightful, and action-oriented.

=== MY PRIORITIES ===
{ctx['my-priorities.md']}

=== MY TEAM & STAKEHOLDERS ===
{ctx['my-team.md']}

=== MY COMMUNICATION STYLE ===
{ctx['communication-style.md']}

Today is {today}.
"""

    if triage_context:
        system_prompt += f"\n=== TODAY'S TRIAGE BRIEF ===\n{triage_context}\n"

    # Build conversation contents
    contents = []
    for turn in conversation_history:
        contents.append(types.Content(
            role=turn["role"],
            parts=[types.Part(text=turn["text"])]
        ))
    contents.append(types.Content(
        role="user",
        parts=[types.Part(text=new_message)]
    ))

    response = client.models.generate_content(
        model=REPLY_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.4,
            max_output_tokens=2048,
        ),
        contents=contents,
    )

    assistant_text = response.text

    # Update history
    updated_history = conversation_history + [
        {"role": "user", "text": new_message},
        {"role": "model", "text": assistant_text},
    ]

    return assistant_text, updated_history


def append_to_weekly_log(triage_output: str) -> Path:
    """
    Append triage output to logs/weekly-log.md.
    This is the equivalent of the post-triage hook.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / "weekly-log.md"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n\n---\n## Triage Log — {timestamp}\n\n{triage_output}\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)

    return log_path
