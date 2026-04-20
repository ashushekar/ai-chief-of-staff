"""
AI Chief of Staff — Main CLI
Powered by Gemini models via google-genai SDK.

Usage:
    python main.py triage          # Run morning triage
    python main.py reply           # Draft an email reply (interactive)
    python main.py chat            # Open-ended chat session
    python main.py review-logs     # Review weekly log with Gemini
    python main.py setup           # Show setup instructions
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Try to load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

try:
    import io
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.prompt import Prompt, Confirm
    from rich.rule import Rule
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from chief_of_staff import (
    run_triage,
    draft_email_reply,
    chat_with_chief_of_staff,
    append_to_weekly_log,
)

# Force UTF-8 on Windows to avoid cp1252 emoji encoding errors
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

if HAS_RICH:
    console = Console()
else:
    console = None


def print_header():
    if HAS_RICH:
        console.print(Panel(
            "[bold cyan]AI Chief of Staff[/bold cyan]\n"
            "[dim]Powered by Gemini · google-genai SDK[/dim]",
            border_style="cyan",
            expand=False,
        ))
    else:
        print("=" * 50)
        print("  AI Chief of Staff -- Powered by Gemini")
        print("=" * 50)


def print_response(text: str, title: str = ""):
    if HAS_RICH:
        if title:
            console.print(Rule(f"[bold]{title}[/bold]", style="cyan"))
        console.print(Markdown(text))
    else:
        if title:
            print(f"\n{'='*50}")
            print(f"  {title}")
            print(f"{'='*50}")
        print(text)


def cmd_triage(demo_mode: bool = False):
    """Run the morning triage command."""
    print_header()

    if HAS_RICH:
        console.print("\n[bold yellow]Running Morning Triage...[/bold yellow]\n")
    else:
        print("\n[Running Morning Triage...]\n")

    if demo_mode:
        # Use demo data instead of live APIs
        emails_text = _load_demo_emails()
        events_text = _load_demo_events()
        if HAS_RICH:
            console.print("[dim]Using demo data (pass no --demo flag for live Gmail/GCal)[/dim]\n")
    else:
        # Fetch live data
        if HAS_RICH:
            with console.status("[dim]Fetching emails from Gmail...[/dim]"):
                emails_text = _fetch_live_emails()
            with console.status("[dim]Fetching calendar events...[/dim]"):
                events_text = _fetch_live_events()
        else:
            print("Fetching emails from Gmail...")
            emails_text = _fetch_live_emails()
            print("Fetching calendar events...")
            events_text = _fetch_live_events()

    # Run Gemini triage
    if HAS_RICH:
        with console.status("[dim]Gemini is analyzing your inbox...[/dim]"):
            triage_output = run_triage(emails_text, events_text)
    else:
        print("Analyzing with Gemini...")
        triage_output = run_triage(emails_text, events_text)

    # Display triage output
    print_response(triage_output, "Morning Triage Brief")

    # Auto-log to weekly-log.md (the "hook" equivalent)
    log_path = append_to_weekly_log(triage_output)
    if HAS_RICH:
        console.print(f"\n[dim]Triage logged to {log_path}[/dim]")
    else:
        print(f"\n[Logged to {log_path}]")

    # Interactive follow-up session
    _run_followup_session(triage_output)


def _run_followup_session(triage_context: str):
    """Run interactive follow-up after triage."""
    if HAS_RICH:
        console.print("\n[bold]What would you like to do?[/bold]")
        console.print("[dim]Type your request, 'reply' to draft a reply, or 'exit' to quit[/dim]\n")
    else:
        print("\nWhat would you like to do? (type 'exit' to quit)")

    history = []
    while True:
        try:
            if HAS_RICH:
                user_input = Prompt.ask("[cyan]You[/cyan]").strip()
            else:
                user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input or user_input.lower() in ("exit", "quit", "q"):
            break

        # Check for email reply trigger
        if any(kw in user_input.lower() for kw in ["draft a reply", "reply to", "write a reply"]):
            if HAS_RICH:
                console.print("\n[dim]Paste the email you want to reply to (type END on a new line when done):[/dim]")
            else:
                print("\nPaste the email content (type END on a new line when done):")

            email_lines = []
            while True:
                try:
                    line = input()
                    if line.strip() == "END":
                        break
                    email_lines.append(line)
                except EOFError:
                    break
            email_content = "\n".join(email_lines)

            if email_content.strip():
                if HAS_RICH:
                    with console.status("[dim]Drafting reply...[/dim]"):
                        reply = draft_email_reply(email_content, intent=user_input)
                else:
                    print("Drafting reply...")
                    reply = draft_email_reply(email_content, intent=user_input)
                print_response(reply, "Email Draft")
                continue

        # General conversation
        if HAS_RICH:
            with console.status("[dim]Thinking...[/dim]"):
                response, history = chat_with_chief_of_staff(
                    history, user_input, triage_context=triage_context
                )
        else:
            response, history = chat_with_chief_of_staff(
                history, user_input, triage_context=triage_context
            )

        print_response(response, "Chief of Staff")


def cmd_reply():
    """Draft an email reply (standalone mode)."""
    print_header()
    if HAS_RICH:
        console.print("\n[bold yellow]Email Reply Drafter[/bold yellow]")
        console.print("[dim]Paste the email you want to reply to (type END on a new line when done):[/dim]\n")
    else:
        print("\n[Email Reply Drafter]")
        print("Paste the email (type END on a new line when done):\n")

    email_lines = []
    while True:
        try:
            line = input()
            if line.strip() == "END":
                break
            email_lines.append(line)
        except EOFError:
            break

    email_content = "\n".join(email_lines)
    if not email_content.strip():
        print("No email content provided.")
        return

    intent = ""
    try:
        if HAS_RICH:
            intent = Prompt.ask(
                "[cyan]What outcome do you want from this reply?[/cyan] [dim](press Enter to skip)[/dim]",
                default=""
            )
        else:
            intent = input("What outcome do you want? (press Enter to skip): ")
    except (KeyboardInterrupt, EOFError):
        pass

    if HAS_RICH:
        with console.status("[dim]Drafting reply...[/dim]"):
            reply = draft_email_reply(email_content, intent=intent)
    else:
        print("Drafting reply...")
        reply = draft_email_reply(email_content, intent=intent)

    print_response(reply, "Email Draft")


def cmd_chat():
    """Start an open-ended chat session with the Chief of Staff."""
    print_header()
    if HAS_RICH:
        console.print("\n[bold yellow]Chat with your Chief of Staff[/bold yellow]")
        console.print("[dim]Ask anything - meeting prep, decisions, priorities, drafts. Type 'exit' to quit.[/dim]\n")
    else:
        print("\n[Chat with Chief of Staff]")
        print("Type 'exit' to quit.\n")

    history = []
    while True:
        try:
            if HAS_RICH:
                user_input = Prompt.ask("[cyan]You[/cyan]").strip()
            else:
                user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input or user_input.lower() in ("exit", "quit", "q"):
            break

        if HAS_RICH:
            with console.status("[dim]Thinking...[/dim]"):
                response, history = chat_with_chief_of_staff(history, user_input)
        else:
            response, history = chat_with_chief_of_staff(history, user_input)

        print_response(response, "Chief of Staff")


def cmd_review_logs():
    """Review weekly log with Gemini and get insights."""
    print_header()
    log_path = Path(__file__).parent / "logs" / "weekly-log.md"

    if not log_path.exists():
        if HAS_RICH:
            console.print("[red]No weekly log found yet. Run /triage first to start logging.[/red]")
        else:
            print("No weekly log found. Run triage first.")
        return

    log_content = log_path.read_text(encoding="utf-8")
    if HAS_RICH:
        console.print(f"\n[bold yellow]Reviewing {log_path.name}...[/bold yellow]")

    review_prompt = f"""Here is my triage log from the past period:

{log_content}

Please analyze:
1. What patterns do you see in where I'm spending time?
2. Where am I spending time that doesn't match my stated priorities?
3. What themes are recurring in my P0/P1 emails?
4. One specific recommendation to improve alignment with my priorities.

Be direct and specific. Don't just summarize — tell me what to do differently."""

    history = []
    if HAS_RICH:
        with console.status("[dim]Analyzing your logs...[/dim]"):
            response, history = chat_with_chief_of_staff(history, review_prompt)
    else:
        response, history = chat_with_chief_of_staff(history, review_prompt)

    print_response(response, "Log Review & Insights")

    # Continue interactive session
    if HAS_RICH:
        console.print("\n[dim]Ask follow-up questions about your log, or type 'exit'[/dim]\n")
    while True:
        try:
            if HAS_RICH:
                user_input = Prompt.ask("[cyan]You[/cyan]").strip()
            else:
                user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not user_input or user_input.lower() in ("exit", "quit"):
            break
        if HAS_RICH:
            with console.status("[dim]Thinking...[/dim]"):
                response, history = chat_with_chief_of_staff(history, user_input)
        else:
            response, history = chat_with_chief_of_staff(history, user_input)
        print_response(response, "Chief of Staff")


def cmd_setup():
    """Show setup instructions."""
    setup_path = Path(__file__).parent / "setup" / "oauth-setup.md"
    if setup_path.exists():
        content = setup_path.read_text(encoding="utf-8")
        print_response(content, "Setup Guide")
    else:
        print("Setup guide not found. See README.md")


def cmd_setup_key():
    """Interactive wizard to set the Gemini API key."""
    print_header()
    if HAS_RICH:
        console.print("\n[bold yellow]Gemini API Key Setup[/bold yellow]")
        console.print("[dim]This saves your API key to the .env file in this directory.[/dim]\n")
        console.print("Steps:")
        console.print("  1. Go to: [link=https://aistudio.google.com/app/apikey]https://aistudio.google.com/app/apikey[/link]")
        console.print("  2. Select project: gen-lang-client-0978668617")
        console.print("  3. Click 'Create API Key'")
        console.print("  4. Paste the key below\n")
    else:
        print("\n[Gemini API Key Setup]")
        print("1. Visit: https://aistudio.google.com/app/apikey")
        print("2. Select project: gen-lang-client-0978668617")
        print("3. Click 'Create API Key'")
        print("4. Paste the key below\n")

    try:
        if HAS_RICH:
            api_key = Prompt.ask("[cyan]Paste your API key[/cyan]").strip()
        else:
            api_key = input("Paste your API key: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nSetup cancelled.")
        return

    if not api_key or not api_key.startswith("AIza"):
        print("\nInvalid key format. Gemini API keys start with 'AIza'.")
        return

    # Save to .env
    env_path = Path(__file__).parent / ".env"
    env_content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""

    if "GEMINI_API_KEY=" in env_content:
        # Replace existing key
        lines = env_content.splitlines()
        new_lines = []
        for line in lines:
            if line.startswith("GEMINI_API_KEY="):
                new_lines.append(f"GEMINI_API_KEY={api_key}")
            else:
                new_lines.append(line)
        env_content = "\n".join(new_lines)
    else:
        env_content += f"\nGEMINI_API_KEY={api_key}\n"

    env_path.write_text(env_content, encoding="utf-8")

    if HAS_RICH:
        console.print(f"\n[green]API key saved to {env_path}[/green]")
        console.print("\nRun your first triage:")
        console.print("  [cyan]python main.py triage --demo[/cyan]  (demo mode)")
        console.print("  [cyan]python main.py triage[/cyan]           (live Gmail/GCal)")
    else:
        print(f"\nAPI key saved to {env_path}")
        print("Run: python main.py triage --demo")

    # Verify the key works
    os.environ["GEMINI_API_KEY"] = api_key
    if HAS_RICH:
        with console.status("[dim]Verifying key with a quick test...[/dim]"):
            _test_api_key(api_key)
    else:
        print("Verifying key...")
        _test_api_key(api_key)


def _test_api_key(api_key: str):
    """Quick test to verify the API key works."""
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Say OK.",
            config=types.GenerateContentConfig(max_output_tokens=5)
        )
        if HAS_RICH:
            console.print(f"[green]Key verified! Gemini responded: {response.text.strip()}[/green]")
        else:
            print(f"Key verified! Gemini: {response.text.strip()}")
    except Exception as e:
        if HAS_RICH:
            console.print(f"[red]Key verification failed: {e}[/red]")
            console.print("[dim]The key was saved but may not be valid. Try again.[/dim]")
        else:
            print(f"Key verification failed: {e}")



def _fetch_live_emails() -> str:
    """Fetch live emails from Gmail."""
    try:
        from gmail_client import fetch_recent_emails, format_emails_for_prompt
        emails = fetch_recent_emails(hours=24)
        return format_emails_for_prompt(emails)
    except ImportError as e:
        return f"Gmail client not available: {e}\nInstall google-auth-oauthlib to enable Gmail integration."
    except Exception as e:
        return f"Could not fetch emails: {e}\nUse demo mode (--demo) or paste emails manually."


def _fetch_live_events() -> str:
    """Fetch live calendar events."""
    try:
        from gcal_client import fetch_todays_events, format_events_for_prompt
        events = fetch_todays_events(lookahead_hours=48)
        return format_events_for_prompt(events)
    except ImportError as e:
        return f"Calendar client not available: {e}"
    except Exception as e:
        return f"Could not fetch calendar events: {e}"


def _load_demo_emails() -> str:
    """Load demo email data for testing without Gmail OAuth."""
    demo_path = Path(__file__).parent / "demo" / "sample-emails.md"
    if demo_path.exists():
        return demo_path.read_text(encoding="utf-8")
    # Built-in fallback demo data
    return """## Emails (5 total)

### Email 1 [UNREAD, IMPORTANT]
From: sarah.chen@company.com (Sarah Chen, VP Product)
Subject: Orion v2 — decision needed on launch scope
Date: Mon, 20 Apr 2026 09:15:00 +0000
Body preview:
Hi, I need a final call on whether we cut the advanced filtering feature from the v2 launch or delay by 2 weeks. Engineering says it adds 10 days. We have Hartwell Group demo on May 5. What's your recommendation?

---

### Email 2 [UNREAD]
From: james.okafor@hartwellgroup.com (James Okafor, Hartwell Group)
Subject: Integration questions before May 5 demo
Date: Mon, 20 Apr 2026 08:30:00 +0000
Body preview:
Following up on our last conversation. We have three integration questions our CTO wants answered before the demo. Can we schedule a technical call this week? We're evaluating a competitor demo on Thursday.

---

### Email 3 [UNREAD]
From: kai.oduya@company.com (Kai Oduya, Senior PM)
Subject: QA blocker — ticket #841 needs your call
Date: Mon, 20 Apr 2026 07:45:00 +0000
Body preview:
The critical bug in the data sync module (#841) is blocked on a product decision: do we patch the existing API or rewrite the connector? Engineering needs an answer today to stay on track for April 15.

---

### Email 4
From: newsletter@productops.io
Subject: 10 frameworks for product roadmap planning
Date: Sun, 19 Apr 2026 18:00:00 +0000
Body preview:
This week we look at 10 proven frameworks product leaders use to prioritize their roadmaps...

---

### Email 5
From: recruiter@talent.co
Subject: Exciting PM opportunity at [Top Startup]
Date: Sun, 19 Apr 2026 14:00:00 +0000
Body preview:
Hi there! I came across your profile and think you'd be a great fit for a Senior PM role...

---"""


def _load_demo_events() -> str:
    """Load demo calendar events for testing."""
    today = datetime.now().strftime("%a %b %d")
    return f"""## Calendar (3 events)

### Standup — Engineering
Time: {today}, 09:30 AM
Attendees: kai.oduya@company.com, priya.nair@company.com
Notes: Daily engineering sync. Orion v2 status.
---

### 1:1 with Sarah Chen
Time: {today}, 11:00 AM
Attendees: sarah.chen@company.com
Notes: Weekly 1:1 with VP Product. Agenda: Orion v2 scope decision, Hartwell update.
---

### AI Roadmap Working Session
Time: {today}, 03:00 PM
Attendees: tom.reyes@company.com, dana.kim@company.com
Notes: Board presentation prep. Need use cases and ROI estimates.
---"""


def main():
    parser = argparse.ArgumentParser(
        description="AI Chief of Staff — Powered by Gemini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  triage        Run morning email & calendar triage
  reply         Draft an email reply (interactive)
  chat          Open-ended chat session
  review-logs   Review weekly log and get insights
  setup         Show OAuth setup instructions

Examples:
  python main.py triage          # Live triage (requires Gmail OAuth)
  python main.py triage --demo   # Demo triage with sample data
  python main.py reply           # Draft a reply
  python main.py chat            # Chat session
  python main.py review-logs     # Analyze your weekly log
        """
    )
    parser.add_argument("command", nargs="?", default="triage",
                        choices=["triage", "reply", "chat", "review-logs", "setup", "setup-key"])
    parser.add_argument("--demo", action="store_true",
                        help="Use demo data instead of live Gmail/GCal (no OAuth needed)")

    args = parser.parse_args()

    try:
        if args.command == "triage":
            cmd_triage(demo_mode=args.demo)
        elif args.command == "reply":
            cmd_reply()
        elif args.command == "chat":
            cmd_chat()
        elif args.command == "review-logs":
            cmd_review_logs()
        elif args.command == "setup":
            cmd_setup()
        elif args.command == "setup-key":
            cmd_setup_key()
    except KeyboardInterrupt:
        if HAS_RICH:
            console.print("\n[dim]Exiting. Goodbye.[/dim]")
        else:
            print("\nExiting.")
        sys.exit(0)
    except Exception as e:
        if HAS_RICH:
            console.print(f"\n[red]Error: {e}[/red]")
        else:
            print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
