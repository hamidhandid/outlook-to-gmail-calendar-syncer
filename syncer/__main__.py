from __future__ import annotations

import argparse
import sys
from textwrap import dedent

from .api import (
    check_tokens_status,
    format_event_row,
    get_events,
    login_exchange,
    reauth_google,
    run_sync,
)
from .config import ConfigError, load_settings
from .schedule import install_schedule, uninstall_schedule

MENU_ACTIONS = [
    ("gui", "Open the graphical app"),
    ("setup", "Interactive Google Cloud + config wizard"),
    ("setup --google-only", "Google OAuth client only"),
    ("login", "Save / update Exchange password in Keychain"),
    ("reauth-google", "Delete Google token and sign in again"),
    ("tokens", "Check Exchange + Google token / login status"),
    ("list-calendars", "List Exchange or Apple calendars"),
    ("check", "Verify config, Exchange, and Google login"),
    ("get", "List Outlook events in the configured date window"),
    ("sync --dry-run", "Preview sync without writing to Google"),
    ("sync", "Copy Outlook events into Google Calendar"),
    ("install-schedule", "Run sync every 15 minutes via launchd"),
    ("uninstall-schedule", "Stop the background schedule"),
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


def cmd_tokens() -> None:
    settings = _settings()
    print("Token / login status\n")
    print(f"config: {settings.config_path}")
    print(f"source: {settings.source}")
    print()
    result = check_tokens_status(settings)
    print(f"Exchange: {'OK' if result.exchange_ok else 'FAIL'}")
    print(f"  {result.exchange_message}")
    if not result.exchange_ok:
        print("  Fix: python -m syncer login")
    print()
    print(f"Google:   {'OK' if result.google_ok else 'FAIL'}")
    print(f"  {result.google_message}")
    if settings.credentials_path.exists():
        print(f"  client: {settings.credentials_path}")
    if settings.token_path.exists():
        print(f"  token:  {settings.token_path}")
    if not result.google_ok:
        print("  Fix: python -m syncer reauth-google")
        print(
            "  Note: OAuth apps left in Testing expire refresh tokens after ~7 days."
        )
    print()
    if result.ok:
        print("Both look good. Run: python -m syncer sync")
    else:
        raise SystemExit(1)


def cmd_check() -> None:
    settings = _settings()
    print(f"config: {settings.config_path}")
    print(f"source: {settings.source}")
    if not settings.credentials_path.exists():
        raise SystemExit(
            "Missing credentials.json. Run: python -m syncer setup --google-only"
        )
    print(f"google oauth client: {settings.credentials_path}")
    result = check_tokens_status(settings)
    if not result.ok:
        raise SystemExit(result.message)
    print("Ready. Run: python -m syncer sync")


def cmd_get() -> None:
    settings = _settings()
    result = get_events(settings)
    if not result.ok:
        raise SystemExit(result.message)
    print(result.message)
    for event in result.events:
        print(f"  {format_event_row(event, settings.privacy, settings.timezone)}")


def cmd_sync(*, dry_run: bool) -> None:
    result = run_sync(_settings(), dry_run=dry_run)
    if not result.ok:
        raise SystemExit(result.message)


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
    elif args.command == "login":
        cmd_login()
    elif args.command == "reauth-google":
        cmd_reauth_google()
    elif args.command == "tokens":
        cmd_tokens()
    elif args.command == "list-calendars":
        cmd_list_calendars()
    elif args.command == "check":
        cmd_check()
    elif args.command == "get":
        cmd_get()
    elif args.command == "sync":
        cmd_sync(dry_run=args.dry_run)
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
    sub.add_parser("login", help="Save Exchange password in Keychain and test the login.")
    sub.add_parser(
        "reauth-google",
        help="Delete token.json and open a browser to sign in to Google again.",
    )
    sub.add_parser(
        "tokens",
        help="Check whether Exchange and Google logins/tokens are still valid.",
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
    sub.add_parser("check", help="Verify Exchange/Calendar access, config, and Google login.")
    sub.add_parser("get", help="List Outlook events in the configured date window.")
    sync_p = sub.add_parser("sync", help="Copy Outlook events into Google Calendar.")
    sync_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing to Google.",
    )
    sub.add_parser("install-schedule", help="Run sync every 15 minutes via launchd.")
    sub.add_parser("uninstall-schedule", help="Stop the background schedule.")
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
