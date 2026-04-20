# OAuth Setup Guide — Gmail & Google Calendar

This guide sets up read-only access to Gmail and Google Calendar for the AI Chief of Staff.

---

## Step 1 — Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **New Project** → name it `chief-of-staff` → Create
3. Select your new project

---

## Step 2 — Enable APIs

In your project, go to **APIs & Services > Library** and enable:
- **Gmail API**
- **Google Calendar API**

---

## Step 3 — Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Application type: **Desktop app**
4. Name: `chief-of-staff-local`
5. Download the JSON file
6. **Rename it to `client_secret.json`**
7. **Copy it to `credentials/client_secret.json`** in this project

---

## Step 4 — Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. User type: **External** (unless you have a Google Workspace org)
3. App name: `Chief of Staff`
4. Add your Gmail address as a test user
5. Add scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/calendar.readonly`
6. Save

---

## Step 5 — First Run (OAuth Flow)

Run your first triage. It will open a browser window asking you to authorize:

```powershell
python main.py triage
```

- Click **Allow** when prompted
- The token will be saved to `credentials/gmail_token.json` and `credentials/gcal_token.json`
- Subsequent runs won't need browser authorization

---

## Step 6 — Set Your Gemini API Key

Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

Option A — Environment variable (recommended):
```powershell
$env:GEMINI_API_KEY = "your-key-here"
```

Option B — `.env` file in the project root:
```
GEMINI_API_KEY=your-key-here
```

---

## Permissions Summary

| What | Scope | Why |
|------|-------|-----|
| Gmail | `gmail.readonly` | Read emails for triage (no send/modify) |
| Calendar | `calendar.readonly` | Read events for daily briefing (no write) |
| Gemini API | API key | Power the LLM analysis |

---

## Testing Without OAuth

Use demo mode to test the system without setting up OAuth:

```powershell
python main.py triage --demo
```

This uses sample emails and events bundled with the project.

---

## Troubleshooting

**"redirect_uri_mismatch" error:** Ensure you created a **Desktop app** credential, not a Web app.

**"Access blocked" error:** Add your email as a test user in the OAuth consent screen.

**Token expired:** Delete `credentials/gmail_token.json` and re-run to re-authenticate.

**No emails fetched:** Check the Gmail API is enabled in your Cloud project.
