from __future__ import annotations

import shutil
import textwrap
import webbrowser
from pathlib import Path

import yaml

from .config import CONFIG_PATH, EXAMPLE_PATH, ROOT

GOOGLE_PROJECT = "https://console.cloud.google.com/projectcreate"
GOOGLE_CALENDAR_API = (
    "https://console.cloud.google.com/apis/library/calendar-json.googleapis.com"
)
GOOGLE_AUTH = "https://console.cloud.google.com/auth/overview"
GOOGLE_AUDIENCE = "https://console.cloud.google.com/auth/audience"
GOOGLE_CLIENTS = "https://console.cloud.google.com/auth/clients"
CREDENTIALS_PATH = ROOT / "credentials.json"


def _hrule() -> None:
    print("\n" + "─" * 64 + "\n")


def _pause(message: str = "Press Enter when that step is done…") -> None:
    input(f"\n{message} ")


def _yes(question: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{question} [{hint}]: ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Please type y or n.")


def _ask(question: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(f"{question}{suffix}: ").strip()
    return raw or default


def _ask_int(question: str, default: int) -> int:
    raw = _ask(question, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def _open(url: str) -> None:
    print(f"\nOpening:\n  {url}\n")
    try:
        webbrowser.open(url, new=2)
    except Exception:
        print("Could not open a browser. Copy the URL above into Chrome or Safari.")


def _find_downloaded_json() -> Path | None:
    downloads = Path.home() / "Downloads"
    if not downloads.is_dir():
        return None
    matches = sorted(
        list(downloads.glob("client_secret_*.json"))
        + list(downloads.glob("*credentials*.json")),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def _copy_credentials() -> bool:
    if CREDENTIALS_PATH.exists():
        print(f"Found {CREDENTIALS_PATH}")
        if _yes("Keep this credentials.json file?", default=True):
            return True
    downloaded = _find_downloaded_json()
    if downloaded:
        print(f"Found a Google client file in Downloads:\n  {downloaded}")
        if _yes("Copy that file here as credentials.json?", default=True):
            shutil.copy2(downloaded, CREDENTIALS_PATH)
            print(f"Saved {CREDENTIALS_PATH}")
            return True
    while True:
        raw = _ask(
            "Paste the full path to the JSON you downloaded (or press Enter to skip)",
            "",
        )
        if not raw:
            return CREDENTIALS_PATH.exists()
        src = Path(raw).expanduser()
        if src.is_file():
            shutil.copy2(src, CREDENTIALS_PATH)
            print(f"Saved {CREDENTIALS_PATH}")
            return True
        print(f"No file at {src}")


def walk_google_oauth() -> None:
    print(
        textwrap.dedent(
            """\
            Google OAuth client (do this once, with the Gmail that should
            receive your work calendar)

            Use a normal browser, signed in to that Gmail. You do not need a
            Google Workspace company account.

            Watch the project picker at the top of Google Cloud Console. Every
            page must show the same project you create in step 1.
            """
        ).rstrip()
    )

    if CREDENTIALS_PATH.exists() and _yes(
        "credentials.json is already in this folder. Skip the Google Cloud steps?",
        default=False,
    ):
        return

    _hrule()
    print("Step 1 — Create a Google Cloud project")
    print(
        textwrap.dedent(
            """\
            1. A page titled “New Project” should open.
            2. Project name: outlook-calendar-sync  (any name is fine)
            3. Click Create.
            4. When it finishes, click the project picker at the top and
               select that project so its name appears in the header.
            """
        ).rstrip()
    )
    _open(GOOGLE_PROJECT)
    _pause()

    _hrule()
    print("Step 2 — Enable the Google Calendar API")
    print(
        textwrap.dedent(
            """\
            1. Confirm the project name at the top is the one you just created.
            2. Click Enable.
            """
        ).rstrip()
    )
    _open(GOOGLE_CALENDAR_API)
    _pause("Press Enter after the Calendar API is enabled…")

    _hrule()
    print("Step 3 — OAuth consent screen (Google Auth Platform)")
    print(
        textwrap.dedent(
            """\
            Google moved this. It is now “Google Auth Platform”, not the old
            “APIs & Services → OAuth consent screen”.

            1. If you see Get started, click it.
            2. App name: Outlook Calendar Sync
            3. User support email: your Gmail
            4. Click Next.
            5. Audience: External
               (Internal is only for a company Google Workspace. Personal
               Gmail must be External.)
            6. Click Next.
            7. Contact email: your Gmail again.
            8. Agree to the user data policy, then Create / Finish.
            """
        ).rstrip()
    )
    _open(GOOGLE_AUTH)
    _pause("Press Enter after the consent screen is created…")

    _hrule()
    print("Step 4 — Add yourself as a test user")
    print(
        textwrap.dedent(
            """\
            While the app is in Testing, only listed accounts can sign in.

            1. Open Audience (the page should open now).
            2. Under Test users, click Add users.
            3. Type your full Gmail address → Save.
            """
        ).rstrip()
    )
    _open(GOOGLE_AUDIENCE)
    _pause("Press Enter after your Gmail is listed as a test user…")

    _hrule()
    print("Step 5 — Create a Desktop OAuth client")
    print(
        textwrap.dedent(
            """\
            1. Click Create client.
            2. Application type: Desktop app
               Do not pick Web application or iOS.
            3. Name: Mac syncer
            4. Click Create.
            5. Click Download JSON (or open the client and download).
            """
        ).rstrip()
    )
    _open(GOOGLE_CLIENTS)
    _pause("Press Enter after the JSON file is downloaded…")

    _hrule()
    print("Step 6 — Save credentials.json in this project")
    print(f"The file must end up at:\n  {CREDENTIALS_PATH}")
    if not _copy_credentials():
        print(
            "\nYou can copy it later with:\n"
            f"  mv ~/Downloads/client_secret_*.json {CREDENTIALS_PATH}"
        )
    print(
        textwrap.dedent(
            """\

            Later, `python -m syncer check` or `sync` will open a browser.
            Choose your Gmail. If you see “Google hasn’t verified this app”,
            that is normal: click Advanced → Go to Outlook Calendar Sync
            (unsafe) → Allow.

            While the app stays in Testing, Google may expire that login
            after 7 days. Run check or sync again to sign in once more.
            """
        ).rstrip()
    )


def _write_config(
    *,
    source: str,
    email: str,
    server: str,
    username: str,
    auth: str,
    calendar: str,
    verify_ssl: bool,
    privacy: str,
    google_calendar: str,
    days_back: int,
    days_forward: int,
    apple_calendar: str,
) -> None:
    payload = {
        "source": source,
        "days_back": days_back,
        "days_forward": days_forward,
        "privacy": privacy,
        "ews": {
            "server": server,
            "email": email,
            "username": username,
            "auth": auth,
            "calendar": calendar,
            "verify_ssl": verify_ssl,
        },
        "apple_calendar": apple_calendar,
        "google_calendar": google_calendar,
        "timezone": "",
    }
    CONFIG_PATH.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def walk_exchange_config() -> None:
    print("Exchange / Outlook connection")
    print(
        "This Mac talks to your mail server over Exchange Web Services.\n"
        "Apple Mail is not required. Connect the company VPN first."
    )
    if CONFIG_PATH.exists():
        print(f"\nExisting config: {CONFIG_PATH}")
        if not _yes("Overwrite config.yaml with answers from this wizard?", default=False):
            return

    email = _ask("Work email address")
    if not email:
        print("Skipping config.yaml. You can copy config.example.yaml later.")
        return
    server = _ask("Exchange host (from OWA, without https://)", "mail.company.com")
    username = _ask(
        "Username (empty = same as email; if login fails try DOMAIN\\account)",
        "",
    )
    auth = _ask("Auth type: ntlm or basic", "ntlm").lower()
    if auth not in {"ntlm", "basic"}:
        auth = "ntlm"
    verify_ssl = _yes(
        "Verify TLS certificates? Choose n if the company uses an internal CA",
        default=True,
    )
    privacy = _ask("Copy full details (full) or only Busy blocks (busy)?", "busy")
    if privacy not in {"full", "busy"}:
        privacy = "busy"
    google_calendar = _ask(
        "Name of the Google calendar to create/use",
        "Work (Outlook)",
    )
    days_back = _ask_int("Days of past events to copy", 7)
    days_forward = _ask_int("Days of future events to copy", 60)
    _write_config(
        source="ews",
        email=email,
        server=server,
        username=username,
        auth=auth,
        calendar="",
        verify_ssl=verify_ssl,
        privacy=privacy,
        google_calendar=google_calendar,
        days_back=days_back,
        days_forward=days_forward,
        apple_calendar="Exchange / Calendar",
    )
    print(f"\nWrote {CONFIG_PATH}")


def run_wizard(*, google_only: bool = False) -> None:
    print(
        textwrap.dedent(
            """\
            Outlook → Google Calendar setup wizard
            ======================================

            This walks you through creating a personal Google Cloud project,
            turning on the Calendar API, and downloading an OAuth client.
            It then writes config.yaml for your Exchange server.
            """
        ).rstrip()
    )
    if not EXAMPLE_PATH.exists():
        raise SystemExit(f"Missing {EXAMPLE_PATH}")
    _pause("Press Enter to start…")
    _hrule()
    walk_google_oauth()
    if google_only:
        print("\nGoogle steps finished.")
        return
    _hrule()
    walk_exchange_config()
    _hrule()
    print("Next commands (VPN on):")
    print(
        textwrap.dedent(
            """\
              python -m syncer login
              python -m syncer check
              python -m syncer sync --dry-run
              python -m syncer sync
              python -m syncer install-schedule   # optional, every 15 minutes
            """
        ).rstrip()
    )
    if CONFIG_PATH.exists() and _yes(
        "Save the Exchange password in Keychain now?", default=True
    ):
        from . import ews
        from .config import load_settings

        settings = load_settings()
        if settings.ews is None:
            print("source is not ews; skipping Exchange login.")
        else:
            ews.prompt_and_save_password(settings.ews.email)
            account = ews.connect(settings.ews)
            print(f"Connected to {settings.ews.server} as {account.primary_smtp_address}")
    if CREDENTIALS_PATH.exists() and _yes(
        "Open the Google sign-in now to test Calendar access?",
        default=True,
    ):
        from .google import google_service

        google_service(CREDENTIALS_PATH, ROOT / "token.json")
        print("google login: ok")
    print("\nSetup finished.")
