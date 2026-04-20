# AI Chief of Staff — Gemini Edition

> **Inspired by [Build your AI Chief of Staff in 45 minutes](https://www.agentrecipes.com/)** (originally Claude Code)
> **Reimplemented** using Google Gemini models (`google-genai` SDK) with Gmail + Google Calendar integration

---

## What this is

A personal AI Chief of Staff that runs locally on your machine and:

1. **Runs a daily triage** of your Gmail + Calendar — prioritised by your actual goals, not inbox order
2. **Drafts email replies** that sound like you (not a generic AI)
3. **Logs every triage automatically** to build a personal work-pattern record
4. **Answers questions** about your day, your decisions, and your priorities

Built for: **Lead Data Scientists, technical team leads, and builders** who need to stay on top of communications without letting their inbox run their day.

---

## Architecture

```
ai-chief-of-staff/
├── main.py                    # CLI entry point
├── chief_of_staff.py          # Gemini orchestration engine
├── gmail_client.py            # Gmail API client (OAuth2, read-only)
├── gcal_client.py             # Google Calendar API client (OAuth2, read-only)
├── setup_oauth.py             # One-click Gmail + Calendar auth wizard
│
├── context/                   # ← The brain. Edit these.
│   ├── my-priorities.md       # Your Q2 goals and what you're NOT doing
│   ├── my-team.md             # Your team, stakeholders, and SLAs
│   └── communication-style.md # Your voice, banned phrases, sign-offs
│
├── skills/
│   └── email-reply/
│       └── SKILL.md           # Email reply skill definition
│
├── logs/
│   └── weekly-log.md          # Auto-generated triage log (gitignored)
│
├── credentials/               # OAuth tokens (gitignored — never committed)
│   ├── client_secret.json     # Your Google Cloud OAuth creds ← ADD THIS
│   ├── gmail_token.json       # Auto-generated after first auth
│   └── gcal_token.json        # Auto-generated after first auth
│
├── setup/
│   └── oauth-setup.md         # Step-by-step OAuth guide
│
├── .env                       # API key (gitignored)
└── .env.example               # Template — copy to .env and fill in
```

---

## Quick Start

### Step 1 — Get a Gemini API key

```powershell
python main.py setup-key
```

Or manually: get a free key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) and add it to `.env`:
```
GEMINI_API_KEY=AIza...
```

### Step 2 — Test with demo data (no auth needed)

```powershell
$env:PYTHONIOENCODING = "utf-8"
python main.py triage --demo
```

### Step 3 — Connect your Gmail + Calendar

Follow `setup/oauth-setup.md`, then run the one-click wizard:
```powershell
python setup_oauth.py
```

This opens a browser window twice (Gmail → Allow, Calendar → Allow). Tokens are cached — you only do this once.

### Step 4 — Run live triage

```powershell
python main.py triage
```

---

## All Commands

| Command | What it does |
|---------|-------------|
| `python main.py triage` | Morning triage: Gmail + Calendar → prioritised brief |
| `python main.py triage --demo` | Same, with built-in sample data (no OAuth needed) |
| `python main.py reply` | Paste an email → get a draft reply in your voice |
| `python main.py chat` | Open-ended conversation with your CoS |
| `python main.py review-logs` | Analyse your weekly triage log for patterns |
| `python main.py setup-key` | Interactive wizard to set your Gemini API key |
| `python main.py setup` | Show the OAuth setup guide |
| `python setup_oauth.py` | Full Gmail + Calendar OAuth setup wizard |

---

## Interactive Triage Session

After triage runs, you stay in a live session. Try:

```
You: draft a reply to the Hartwell email
You: who should I call first today?
You: what's blocking my Q2 milestone?
You: write a decline to the newsletter
You: prep me for my 3pm meeting
```

---

## The Context Files — Fill These In

This is the **highest-leverage step**. The triage is only as good as your context:

| File | What to add | Takes |
|------|-------------|-------|
| `context/my-priorities.md` | Your Q2 goals, deadlines, what you're NOT doing | 10 min |
| `context/my-team.md` | Manager, team, key stakeholders + urgency levels | 10 min |
| `context/communication-style.md` | Your writing rules, banned phrases, sign-off | 5 min |

Once filled in, **you never configure the triage again** — just run it each morning.

---

## How It Works

```
Morning
  │
  ▼
python main.py triage
  │
  ├── Reads context/ (your priorities, team, style)
  ├── Fetches Gmail (last 24h unread/important)
  ├── Fetches Calendar (next 48h events)
  │
  ├── Gemini 2.5 Flash → prioritised brief
  │   P0 / P1 / P2 / Archived
  │   Calendar events annotated with email context
  │
  ├── Auto-logged to logs/weekly-log.md
  │
  └── Interactive session
        "draft a reply to X" → Gemini 2.5 Pro email draft
        "help me decide Y"   → CoS reasoning with full context
```

---

## Models

| Task | Model | Why |
|------|-------|-----|
| Morning triage | `gemini-2.5-flash` | Fast, cost-effective for daily use |
| Email drafts | `gemini-2.5-pro` | Highest quality for writing |
| Chat / log review | `gemini-2.5-pro` | Nuanced reasoning |

Override via `.env`:
```
TRIAGE_MODEL=gemini-2.5-flash
REPLY_MODEL=gemini-2.5-pro
```

---

## Dependencies

Uses the existing `pbkyc` virtual environment:

```powershell
# Run with pbkyc venv
c:\Study\pbkyc\.venv\Scripts\python.exe main.py triage

# Or activate venv first
c:\Study\pbkyc\.venv\Scripts\Activate.ps1
python main.py triage
```

Key packages (all already installed in pbkyc venv):
- `google-genai >= 1.62.0`
- `google-auth-oauthlib`
- `google-api-python-client`
- `rich`
- `python-dotenv`

---

## Security

- `.env` is gitignored — your API key never hits the repo
- `credentials/` is gitignored — OAuth tokens stay local
- Gmail and Calendar access is **read-only** — the system cannot send, delete, or modify anything
- No data leaves your machine except API calls to Gemini and Google OAuth

---

## Keeping the System Sharp

- **Update `my-priorities.md`** each quarter or when your focus shifts
- **Refine `communication-style.md`** when a draft sounds wrong — rule of thumb: if you correct Gemini twice on the same thing, add it to the file
- **Run `review-logs` monthly** — ask "where am I spending time that doesn't match my stated priorities?"
