from __future__ import annotations

import argparse
import sys
from textwrap import dedent

from pathlib import Path

from .api import (
    check_google_auth,
    check_outlook_auth,
    format_event_row,
    get_events,
    login_exchange,
    reauth_google,
    reset_credentials_and_calendar,
    run_sync,
    run_sync_from_encrypted,
    store_events_encrypted,
)
from .config import ConfigError, load_settings
from .encrypted_store import default_store_path
from .schedule import install_schedule, uninstall_schedule

MENU_ACTIONS = [
    ("gui", "Open the graphical app"),
    ("setup", "Interactive Google Cloud + config wizard"),
    ("setup --google-only", "Google OAuth client only"),
    ("login-to-outlook", "Save / update Exchange password in the system keyring"),
    ("reauth-google", "Delete Google token and sign in again"),
    ("check-outlook-auth", "Check Outlook / Exchange login"),
    ("list-calendars", "List Exchange or Apple calendars"),
    ("check-google-auth", "Check Google OAuth / token status"),
    ("show-outlook-events", "List Outlook events in the configured date window"),
    ("sync --dry-run", "Preview sync without writing to Google"),
    ("sync", "Copy Outlook events into Google Calendar"),
    ("install-schedule", "Run sync every 15 minutes (launchd / Task Scheduler / systemd)"),
    ("uninstall-schedule", "Stop the background schedule"),
    # New options stay at the end so existing menu numbers do not shift.
    ("store", "Fetch Outlook events and save them to an encrypted file"),
    ("sync-stored --dry-run", "Preview sync from the encrypted file (no Outlook fetch)"),
    ("sync-stored", "Sync Google Calendar from a previously encrypted events file"),
    ("reset", "Delete Google sync calendar + all Outlook/Google credentials (asks first)"),
]


def _settings():
    try:
        return load_settings()
    except ConfigError as exc:
        raise SystemExit(str(exc)) from exc


def cmd_list_calendars() -> None:
    settings = _settings()
    if settings.source == "ews":
        from . import ews

        assert settings.ews is not None
        account = ews.connect(settings.ews)
        print(f"Exchange calendars on {settings.ews.server} as {settings.ews.email}:\n")
        found = ews.list_calendars(account)
        if not found:
            print("  (none found — the default mailbox calendar will still be used)")
            return
        for info in found:
            print(f"  {info.label}")
        print("\nCopy one of those names into config.yaml as ews.calendar, or leave it empty.")
        return

    from . import apple

    print("Apple calendars this Mac can read:\n")
    for info in apple.list_calendars():
        print(f"  {info.label}")
        print(f"      id: {info.identifier}")
    print('\nCopy the "Account / Calendar" line of your Outlook calendar into config.yaml.')


def cmd_login() -> None:
    ok, msg = login_exchange()
    if not ok:
        raise SystemExit(msg)
    print(msg)


def cmd_reauth_google() -> None:
    ok, msg = reauth_google()
    if not ok:
        raise SystemExit(msg)
    print(msg)


def cmd_check_outlook_auth() -> None:
    settings = _settings()
    print(f"config: {settings.config_path}")
    print(f"source: {settings.source}")
    ok, msg = check_outlook_auth(settings)
    print(f"Outlook: {'OK' if ok else 'FAIL'}")
    print(f"  {msg}")
    if not ok:
        print("  Fix: python -m syncer login-to-outlook")
        raise SystemExit(1)


def cmd_check_google_auth() -> None:
    settings = _settings()
    print(f"config: {settings.config_path}")
    if settings.credentials_path.exists():
        print(f"client: {settings.credentials_path}")
    if settings.token_path.exists():
        print(f"token:  {settings.token_path}")
    ok, msg = check_google_auth(settings)
    print(f"Google: {'OK' if ok else 'FAIL'}")
    print(f"  {msg}")
    if not ok:
        print("  Fix: python -m syncer reauth-google")
        print(
            "  Note: OAuth apps left in Testing expire refresh tokens after ~7 days."
        )
        raise SystemExit(1)


def cmd_get() -> None:
    settings = _settings()
    result = get_events(settings)
    if not result.ok:
        raise SystemExit(result.message)
    print(result.message)
    for event in result.events:
        print(f"  {format_event_row(event, settings.privacy, settings.timezone)}")


def cmd_store(*, output: Path | None) -> None:
    settings = _settings()
    result = store_events_encrypted(settings, path=output)
    if not result.ok:
        raise SystemExit(result.message)
    print(result.message)


def cmd_sync(*, dry_run: bool) -> None:
    result = run_sync(_settings(), dry_run=dry_run)
    if not result.ok:
        raise SystemExit(result.message)


def cmd_sync_stored(*, input_path: Path | None, dry_run: bool) -> None:
    result = run_sync_from_encrypted(
        _settings(),
        path=input_path,
        dry_run=dry_run,
    )
    if not result.ok:
        raise SystemExit(result.message)


def cmd_reset(*, yes: bool, keep_calendar: bool) -> None:
    try:
        settings = load_settings()
        cal_name = settings.google_calendar
        email = settings.ews.email if settings.ews else "(unknown)"
    except ConfigError:
        settings = None
        cal_name = "Work (Outlook)"
        email = "(from config if present)"

    print(
        "WARNING: This will permanently remove:\n"
        f"  • Google Calendar named {cal_name!r} (unless --keep-calendar)\n"
        "  • credentials.json and token.json (Google OAuth)\n"
        "  • events.enc (encrypted Outlook snapshot), if present\n"
        f"  • Exchange password for {email} from the OS keyring\n"
        "\n"
        "config.yaml is NOT deleted.\n"
    )
    if not yes:
        answer = input('Type DELETE to confirm (or press Enter to cancel): ').strip()
        if answer != "DELETE":
            raise SystemExit("Reset cancelled.")
    result = reset_credentials_and_calendar(
        settings,
        delete_google_calendar=not keep_calendar,
        confirmed=True,
    )
    print(result.message)
    if not result.ok:
        raise SystemExit(1)


def cmd_gui() -> None:
    from .gui import run_gui

    run_gui()


def _print_menu() -> None:
    print(
        dedent(
            """\
            outlook-to-gmail-calendar-syncer
            ================================

            Enter the number of an option (for example: 11 for sync).
            You can also run the same action later as:
              python -m syncer <command>
            """
        ).rstrip()
    )
    print()
    for index, (command, help_text) in enumerate(MENU_ACTIONS, start=1):
        print(f"  [{index}]  {command}")
        print(f"       {help_text}")
    print("  [0]  quit")
    print()


def run_menu() -> None:
    while True:
        _print_menu()
        raw = input(f"Enter a number (0-{len(MENU_ACTIONS)}): ").strip()
        if not raw:
            print("Please type a number.\n")
            continue
        try:
            choice = int(raw)
        except ValueError:
            print(f"'{raw}' is not a number. Type a number like 1 or 9.\n")
            continue
        if choice == 0:
            print("Bye.")
            return
        if choice < 1 or choice > len(MENU_ACTIONS):
            print(f"No option {choice}. Choose 0–{len(MENU_ACTIONS)}.\n")
            continue
        command = MENU_ACTIONS[choice - 1][0]
        print(f"\n→ [{choice}] python -m syncer {command}\n")
        try:
            dispatch(build_parser().parse_args(command.split()))
        except SystemExit as exc:
            code = exc.code
            if isinstance(code, str) and code:
                print(code)
            elif code not in (0, None):
                print(f"Command failed (exit {code}).")
        except Exception as exc:
            print(f"Command failed: {exc}")
        print()
        again = input("Back to menu? [Y/n]: ").strip().lower()
        if again in {"n", "no"}:
            return
        print()


def dispatch(args: argparse.Namespace) -> None:
    if args.command == "gui":
        cmd_gui()
    elif args.command == "setup":
        from .wizard import run_wizard

        run_wizard(google_only=args.google_only)
    elif args.command == "login-to-outlook":
        cmd_login()
    elif args.command == "reauth-google":
        cmd_reauth_google()
    elif args.command == "check-outlook-auth":
        cmd_check_outlook_auth()
    elif args.command == "list-calendars":
        cmd_list_calendars()
    elif args.command == "check-google-auth":
        cmd_check_google_auth()
    elif args.command == "show-outlook-events":
        cmd_get()
    elif args.command == "store":
        cmd_store(output=args.output)
    elif args.command == "sync":
        cmd_sync(dry_run=args.dry_run)
    elif args.command == "sync-stored":
        cmd_sync_stored(input_path=args.input, dry_run=args.dry_run)
    elif args.command == "reset":
        cmd_reset(yes=args.yes, keep_calendar=args.keep_calendar)
    elif args.command == "install-schedule":
        install_schedule()
    elif args.command == "uninstall-schedule":
        uninstall_schedule()
    else:
        raise SystemExit(f"Unknown command: {args.command}")


def build_parser() -> argparse.ArgumentParser:
    from . import __version__

    parser = argparse.ArgumentParser(
        prog="python -m syncer",
        description=(
            "Copy Outlook/Exchange events into Google Calendar. "
            "Run `python -m syncer gui` for the app, or no arguments for a numbered menu."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("gui", help="Open the CustomTkinter desktop app.")
    sub.add_parser(
        "login-to-outlook",
        help="Save Exchange password in the system keyring and test the login.",
    )
    sub.add_parser(
        "reauth-google",
        help="Delete token.json and open a browser to sign in to Google again.",
    )
    sub.add_parser(
        "check-outlook-auth",
        help="Test Outlook / Exchange login with the saved password.",
    )
    setup_p = sub.add_parser(
        "setup",
        help="Interactive wizard: Google Cloud OAuth, Calendar API, and config.yaml.",
    )
    setup_p.add_argument(
        "--google-only",
        action="store_true",
        help="Only walk through creating the Google OAuth client.",
    )
    sub.add_parser("list-calendars", help="Show Exchange or Apple calendar names.")
    sub.add_parser(
        "check-google-auth",
        help="Test Google OAuth credentials and token.json.",
    )
    sub.add_parser(
        "show-outlook-events",
        help="List Outlook events in the configured date window.",
    )
    store_p = sub.add_parser(
        "store",
        help="Fetch Outlook events and save them to a password-encrypted file (default: events.enc).",
    )
    store_p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help=f"Output path (default: {default_store_path()})",
    )
    sync_p = sub.add_parser("sync", help="Copy Outlook events into Google Calendar.")
    sync_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing to Google.",
    )
    sync_stored_p = sub.add_parser(
        "sync-stored",
        help="Decrypt a previously stored events file and sync it to Google Calendar.",
    )
    sync_stored_p.add_argument(
        "-i",
        "--input",
        type=Path,
        default=None,
        help=f"Encrypted file path (default: {default_store_path()})",
    )
    sync_stored_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing to Google.",
    )
    sub.add_parser(
        "install-schedule",
        help="Run sync every 15 minutes (macOS launchd, Windows Task Scheduler, or Linux systemd --user).",
    )
    sub.add_parser("uninstall-schedule", help="Stop the background schedule.")
    reset_p = sub.add_parser(
        "reset",
        help=(
            "Delete the Google sync calendar and wipe Outlook/Google credentials "
            "(requires typing DELETE unless --yes)."
        ),
    )
    reset_p.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive DELETE confirmation (still destructive).",
    )
    reset_p.add_argument(
        "--keep-calendar",
        action="store_true",
        help="Do not delete the Google Calendar; only wipe local credentials/tokens.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        run_menu()
        return
    dispatch(args)


if __name__ == "__main__":
    main()
