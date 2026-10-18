from __future__ import annotations

import json
import shutil
import textwrap
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from .config import CONFIG_PATH, EXAMPLE_PATH, ROOT
from .paths import bundle_dir

GOOGLE_PROJECT = "https://console.cloud.google.com/projectcreate"
GOOGLE_CALENDAR_API = (
    "https://console.cloud.google.com/apis/library/calendar-json.googleapis.com"
)
GOOGLE_AUTH = "https://console.cloud.google.com/auth/overview"
GOOGLE_BRANDING = "https://console.cloud.google.com/auth/branding"
GOOGLE_AUDIENCE = "https://console.cloud.google.com/auth/audience"
GOOGLE_CLIENTS = "https://console.cloud.google.com/auth/clients"
GOOGLE_CLIENTS_CREATE = "https://console.cloud.google.com/auth/clients/create"

PROGRESS_PATH = ROOT / "google_setup_progress.json"


@dataclass(frozen=True)
class GoogleSetupStep:
    id: str
    title: str
    instructions: str
    url: str | None
    screenshot: str | None  # filename under docs/assets/google-setup/


# Maps to docs/FIRST_TIME_FA.md Steps 1–6 (GUI expands Step 3–5).
GOOGLE_SETUP_STEPS: list[GoogleSetupStep] = [
    GoogleSetupStep(
        id="create_project",
        title="Step 1 — Create a Google Cloud project",
        instructions=(
            "A browser page will open.\n"
            "1. Project name: outlook-calendar-sync (any name is fine)\n"
            "2. Click Create\n"
            "3. Select that project in the top project picker\n\n"
            "If you leave now, click Setup Google again to resume at this step.\n"
            "Confirm when done."
        ),
        url=GOOGLE_PROJECT,
        screenshot="step-01.png",
    ),
    GoogleSetupStep(
        id="enable_calendar_api",
        title="Step 2 — Enable Calendar API",
        instructions=(
            "Confirm the project name at the top, then click Enable.\n\n"
            "If you leave now, click Setup Google again to resume at this step.\n"
            "Confirm when the API is enabled."
        ),
        url=GOOGLE_CALENDAR_API,
        screenshot="step-02.png",
    ),
    GoogleSetupStep(
        id="oauth_get_started",
        title="Step 3 — Get started",
        instructions=(
            "If you see Google Auth Platform not configured yet, click Get started.\n\n"
            "If you leave now, click Setup Google again to resume at this step.\n"
            "Confirm when the Project configuration wizard opens."
        ),
        url=GOOGLE_AUTH,
        screenshot="step-03.png",
    ),
    GoogleSetupStep(
        id="oauth_app_info",
        title="Step 3 — App name & support email",
        instructions=(
            "On App Information:\n"
            "1. App name: Outlook Calendar Sync\n"
            "2. User support email: pick your Gmail "
            "(example@gmail.com in the screenshot)\n"
            "3. Click Next\n\n"
            "If you leave now, click Setup Google again to resume at this step.\n"
            "Confirm when done."
        ),
        url=GOOGLE_AUTH,
        screenshot="step-04.png",
    ),
    GoogleSetupStep(
        id="oauth_audience",
        title="Step 3 — Audience: External",
        instructions=(
            "On Audience:\n"
            "1. Select External "
            "(required for personal Gmail; Internal is only for Google Workspace)\n"
            "2. Click Next\n\n"
            "If you leave now, click Setup Google again to resume at this step.\n"
            "Confirm when done."
        ),
        url=GOOGLE_AUTH,
        screenshot="step-05.png",
    ),
    GoogleSetupStep(
        id="oauth_contact",
        title="Step 3 — Contact Information",
        instructions=(
            "On Contact Information:\n"
            "1. Enter your Gmail again (example@gmail.com in the screenshot)\n"
            "2. Click Next\n\n"
            "If you leave now, click Setup Google again to resume at this step.\n"
            "Confirm when done."
        ),
        url=GOOGLE_AUTH,
        screenshot="step-06.png",
    ),
    GoogleSetupStep(
        id="oauth_finish",
        title="Step 3 — Finish / Create",
        instructions=(
            "On Finish:\n"
            "1. Check I agree to the Google API Services: User Data Policy\n"
            "2. Click Continue if shown\n"
            "3. Click Create\n\n"
            "If you leave now, click Setup Google again to resume at this step.\n"
            "Confirm when OAuth configuration is created."
        ),
        url=GOOGLE_AUTH,
        screenshot="step-07.png",
    ),
    GoogleSetupStep(
        id="test_user_add",
        title="Step 4 — Click Add users",
        instructions=(
            "Under Test users, click + Add users.\n\n"
            "If you leave now, click Setup Google again to resume at this step.\n"
            "Confirm when the Add users panel is open."
        ),
        url=GOOGLE_AUDIENCE,
        screenshot="step-08.png",
    ),
    GoogleSetupStep(
        id="test_user_save",
        title="Step 4 — Type Gmail and Save",
        instructions=(
            "1. Type your full Gmail (example@gmail.com in the screenshot)\n"
            "2. Press Enter so it becomes a chip\n"
            "3. Click Save\n\n"
            "If you leave now, click Setup Google again to resume at this step.\n"
            "Confirm when done."
        ),
        url=GOOGLE_AUDIENCE,
        screenshot="step-09.png",
    ),
    GoogleSetupStep(
        id="create_client",
        title="Step 5 — Create client",
        instructions=(
            "On the Clients page, click Create client.\n\n"
            "If you leave now, click Setup Google again to resume at this step.\n"
            "Confirm when the Create OAuth client ID form is open."
        ),
        url=GOOGLE_CLIENTS,
        screenshot="step-10.png",
    ),
    GoogleSetupStep(
        id="desktop_client",
        title="Step 5 — Desktop app + name",
        instructions=(
            "1. Application type: Desktop app (not Web, not iOS)\n"
            "2. Name: Mac syncer\n"
            "3. Click Create\n\n"
            "If you leave now, click Setup Google again to resume at this step.\n"
            "Confirm when the OAuth client created dialog appears."
        ),
        url=GOOGLE_CLIENTS_CREATE,
        screenshot="step-11.png",
    ),
    GoogleSetupStep(
        id="download_json",
        title="Step 5 — Download JSON",
        instructions=(
            "In the OAuth client created dialog, click Download JSON.\n"
            "Keep that file — you need it in the next step.\n\n"
            "If you leave now, click Setup Google again to resume at this step.\n"
            "Confirm when the JSON is downloaded."
        ),
        url=GOOGLE_CLIENTS,
        screenshot="step-12.png",
    ),
    GoogleSetupStep(
        id="save_credentials",
        title="Step 6 — Save credentials.json",
        instructions=(
            "Copy the downloaded Desktop OAuth client JSON to credentials.json "
            "in the app data folder (Import credentials in the GUI, or confirm "
            "if a recent download was found).\n\n"
            "Confirm when credentials.json is in place."
        ),
        url=None,
        screenshot="step-13.png",
    ),
]


def _credentials_path() -> Path:
    return ROOT / "credentials.json"


# Kept for older imports; always points at the writable data dir.
CREDENTIALS_PATH = _credentials_path()


def google_setup_screenshot_path(filename: str | None) -> Path | None:
    if not filename:
        return None
    for base in (bundle_dir() / "docs" / "assets" / "google-setup", Path(__file__).resolve().parent.parent / "docs" / "assets" / "google-setup"):
        path = base / filename
        if path.is_file():
            return path
    return None


def load_google_setup_progress() -> dict[str, Any] | None:
    if not PROGRESS_PATH.exists():
        return None
    try:
        data = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or "step_id" not in data:
        return None
    return data


def save_google_setup_progress(step_id: str) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.write_text(
        json.dumps(
            {
                "step_id": step_id,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def clear_google_setup_progress() -> None:
    try:
        if PROGRESS_PATH.exists():
            PROGRESS_PATH.unlink()
    except OSError:
        pass


def _step_index(step_id: str) -> int:
    for i, step in enumerate(GOOGLE_SETUP_STEPS):
        if step.id == step_id:
            return i
    return 0


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


def walk_google_oauth_gui(
    *,
    ask_continue: Callable[..., bool],
    ask_step: Callable[[GoogleSetupStep], bool] | None = None,
    log=None,
) -> bool:
    """Browser-based Google OAuth setup for the GUI (no Terminal input).

    ask_continue(title, message) -> bool — plain Confirm/Cancel.
    ask_step(step) -> bool — richer step dialog (URL, screenshot, Open link).
    Falls back to ask_continue when ask_step is omitted.
    """

    def _log(msg: str) -> None:
        if log:
            log("info", msg)

    def _ask_step(step: GoogleSetupStep) -> bool:
        if ask_step is not None:
            return bool(ask_step(step))
        body = step.instructions
        if step.url:
            body = f"{body}\n\nURL:\n{step.url}"
        return bool(ask_continue(step.title, body))

    if _credentials_path().exists():
        if not ask_continue(
            "Setup Google",
            "credentials.json already exists.\n"
            "Continue and walk through Google Cloud again?",
        ):
            return True
        clear_google_setup_progress()

    start_index = 0
    progress = load_google_setup_progress()
    if progress is not None:
        idx = _step_index(str(progress["step_id"]))
        step = GOOGLE_SETUP_STEPS[idx]
        choice = ask_continue(
            "Resume Google setup?",
            f"You left off at:\n{step.title}\n\n"
            "Confirm = continue from that step.\n"
            "Cancel = start over from Step 1.",
        )
        if choice:
            start_index = idx
            _log(f"Resuming Google setup at {step.id}")
        else:
            clear_google_setup_progress()
            start_index = 0
            _log("Starting Google setup from Step 1.")

    for step in GOOGLE_SETUP_STEPS[start_index:]:
        save_google_setup_progress(step.id)
        if step.id == "save_credentials":
            dest = _credentials_path()
            downloaded = _find_downloaded_json()
            if downloaded is not None:
                if ask_continue(
                    step.title,
                    f"{step.instructions}\n\n"
                    f"Found downloaded client file:\n{downloaded}\n\n"
                    f"Copy it to:\n{dest} ?",
                ):
                    shutil.copy2(downloaded, dest)
                    _log(f"Saved {dest}")
                    clear_google_setup_progress()
                    return True
            if not _ask_step(step):
                _log(
                    "Google setup paused. Click Setup Google again to resume "
                    f"at {step.title}."
                )
                return False
            if dest.exists():
                clear_google_setup_progress()
                return True
            _log(
                f"credentials.json still missing at {dest}. "
                "Use Import credentials, then click Setup Google again."
            )
            return False

        if step.url:
            _log(f"Opening: {step.url}")
            try:
                webbrowser.open(step.url, new=2)
            except Exception:
                pass
        if not _ask_step(step):
            _log(
                "Google setup paused. Click Setup Google again to resume "
                f"at {step.title}."
            )
            return False

    clear_google_setup_progress()
    return _credentials_path().exists()


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

    start_index = 0
    progress = load_google_setup_progress()
    if progress is not None:
        idx = _step_index(str(progress["step_id"]))
        step = GOOGLE_SETUP_STEPS[idx]
        print(f"\nSaved progress: {step.title}")
        if _yes("Continue from that step?", default=True):
            start_index = idx
        else:
            clear_google_setup_progress()

    for step in GOOGLE_SETUP_STEPS[start_index:]:
        save_google_setup_progress(step.id)
        _hrule()
        print(step.title)
        print(step.instructions)
        if step.url:
            _open(step.url)
        if step.id == "save_credentials":
            print(f"The file must end up at:\n  {CREDENTIALS_PATH}")
            if not _copy_credentials():
                print(
                    "\nYou can copy it later with:\n"
                    f"  mv ~/Downloads/client_secret_*.json {CREDENTIALS_PATH}"
                )
                print(
                    "\nTo resume later, run setup again — it will return to this step."
                )
                return
            clear_google_setup_progress()
            break
        _pause(
            "Press Enter when done (or Ctrl+C to pause — run setup again to resume)…"
        )

    clear_google_setup_progress()
    print(
        textwrap.dedent(
            """\

            Later, `python -m syncer check-google-auth` or `sync` will open a browser.
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
        "This computer talks to your mail server over Exchange Web Services.\n"
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
    server = _ask("Exchange host (from OWA, without https://)", "mail.digikala.com")
    username = _ask(
        "Username (empty = same as email; if login fails try DOMAIN\\account)",
        "",
    )
    auth = _ask("Auth type: ntlm or basic", "ntlm").lower()
    if auth not in {"ntlm", "basic"}:
        auth = "ntlm"
    verify_ssl = _yes(
        "Verify TLS certificates? Choose n if the company uses an internal CA",
        default=False,
    )
    privacy = _ask("Copy full details (full) or only Busy blocks (busy)?", "full")
    if privacy not in {"full", "busy"}:
        privacy = "full"
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
              python -m syncer login-to-outlook
              python -m syncer check
              python -m syncer sync --dry-run
              python -m syncer sync
              python -m syncer install-schedule   # optional, every 15 minutes
            """
        ).rstrip()
    )
    if CONFIG_PATH.exists() and _yes(
        "Save the Exchange password in the system keyring now?", default=True
    ):
        from . import ews
        from .config import ConfigError, load_settings

        try:
            settings = load_settings()
        except ConfigError as exc:
            print(exc)
            settings = None
        if settings is None or settings.ews is None:
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
