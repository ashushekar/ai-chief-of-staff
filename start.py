"""
start.py — Single command to launch the AI Chief of Staff web app.

Usage:
    c:\Study\pbkyc\.venv\Scripts\python.exe start.py

Starts:
  - FastAPI backend  → http://localhost:8000
  - Next.js frontend → http://localhost:3000
  - Opens browser automatically
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

ROOT = Path(__file__).parent
WEB  = ROOT / "web"
PYTHON = sys.executable

CYAN  = "\033[96m"
GREEN = "\033[92m"
DIM   = "\033[2m"
RESET = "\033[0m"
BOLD  = "\033[1m"

def print_banner():
    print(f"\n{BOLD}{CYAN}")
    print("  ✦  AI Chief of Staff")
    print(f"{RESET}{DIM}  Powered by Gemini · google-genai SDK{RESET}\n")

def wait_for_server(url: str, timeout: int = 30) -> bool:
    import urllib.request, urllib.error
    for _ in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(1)
    return False

def main():
    print_banner()
    processes = []

    try:
        # ── 1. FastAPI backend ───────────────────────────────────────────────
        print(f"  {DIM}Starting API server (port 8000)...{RESET}")
        api_proc = subprocess.Popen(
            [PYTHON, "-m", "uvicorn", "api.server:app", "--port", "8000", "--reload"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processes.append(api_proc)

        # ── 2. Next.js frontend ──────────────────────────────────────────────
        print(f"  {DIM}Starting web frontend (port 3000)...{RESET}")
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        web_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=WEB,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processes.append(web_proc)

        # ── 3. Wait for both to be ready ─────────────────────────────────────
        print(f"  {DIM}Waiting for servers to be ready...{RESET}", end="", flush=True)
        api_up  = wait_for_server("http://localhost:8000/api/health")
        web_up  = wait_for_server("http://localhost:3000")
        print(f" done\n")

        # ── 4. Print status ───────────────────────────────────────────────────
        print(f"  {GREEN}▸ API   →  http://localhost:8000{RESET}  {'✓' if api_up else '✗ (check logs)'}")
        print(f"  {GREEN}▸ App   →  http://localhost:3000{RESET}  {'✓' if web_up else '✗ (check logs)'}")
        print(f"\n  {DIM}Press Ctrl+C to stop both servers{RESET}\n")

        # ── 5. Open browser ───────────────────────────────────────────────────
        if web_up:
            import webbrowser
            webbrowser.open("http://localhost:3000")

        # ── 6. Keep alive until Ctrl+C ────────────────────────────────────────
        while True:
            time.sleep(1)
            # Restart if either process dies unexpectedly
            if api_proc.poll() is not None:
                print(f"\n  {CYAN}Restarting API server...{RESET}")
                api_proc = subprocess.Popen(
                    [PYTHON, "-m", "uvicorn", "api.server:app", "--port", "8000", "--reload"],
                    cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                processes[0] = api_proc

    except KeyboardInterrupt:
        print(f"\n\n  {DIM}Shutting down...{RESET}")
    finally:
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                try: p.kill()
                except Exception: pass
        print(f"  {DIM}Stopped. Goodbye.{RESET}\n")

if __name__ == "__main__":
    main()
