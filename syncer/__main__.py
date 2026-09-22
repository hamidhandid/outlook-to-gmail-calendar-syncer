from __future__ import annotations

import argparse
import sys
from textwrap import dedent

from .config import load_settings
from .google import check_google_token, clear_google_token, google_service
from .schedule import install_schedule, uninstall_schedule
from .sync import sync

MENU_ACTIONS = [
    ("setup", "Interactive Google Cloud + config wizard"),
    ("setup --google-only", "Google OAuth client only"),
    ("login", "Save / update Exchange password in Keychain"),
    ("reauth-google", "Delete Google token and sign in again"),
    ("tokens", "Check Exchange + Google token / login status"),
    ("list-calendars", "List Exchange or Apple calendars"),
    ("check", "Verify config, Exchange, and Google login"),
    ("sync --dry-run", "Preview sync without writing to Google"),
    ("sync", "Copy Outlook events into Google Calendar"),
    ("install-schedule", "Run sync every 15 minutes via launchd"),
    ("uninstall-schedule", "Stop the background schedule"),
]


def cmd_list_calendars() -> None:
    settings = load_settings()
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
    settings = load_settings()
    if settings.source != "ews" or settings.ews is None:
        raise SystemExit("login is only used with source: ews in config.yaml")
    from . import ews

    ews.prompt_and_save_password(settings.ews.email)
    account = ews.connect(settings.ews)
    print(f"Connected to {settings.ews.server} as {account.primary_smtp_address}")


def cmd_reauth_google() -> None:
    settings = load_settings()
    if not settings.credentials_path.exists():
        raise SystemExit(
            "Missing credentials.json. Run: python -m syncer setup --google-only"
        )
    if clear_google_token(settings.token_path):
        print(f"Removed old token: {settings.token_path}")
    google_service(
        settings.credentials_path, settings.token_path, force_reauth=True
    )
    print("Google login: ok")


def _check_exchange() -> tuple[bool, str]:
    settings = load_settings()
    if settings.source != "ews" or settings.ews is None:
        return True, f"source={settings.source} (no Exchange password required)"
    from . import ews

    try:
        ews.password_for(settings.ews.email)
    except SystemExit as exc:
        return False, str(exc).split("\n")[0]
    try:
        account = ews.connect(settings.ews)
        return True, f"ok ({account.primary_smtp_address} on {settings.ews.server})"
    except SystemExit as exc:
        return False, str(exc).split("\n")[0]


def cmd_tokens() -> None:
    settings = load_settings()
    print("Token / login status\n")

    print(f"config: {settings.config_path}")
    print(f"source: {settings.source}")
    print()

    exchange_ok, exchange_msg = _check_exchange()
    print(f"Exchange: {'OK' if exchange_ok else 'FAIL'}")
    print(f"  {exchange_msg}")
    if not exchange_ok:
        print("  Fix: python -m syncer login")
    print()

    google_ok, google_msg = check_google_token(
        settings.credentials_path, settings.token_path
    )
    print(f"Google:   {'OK' if google_ok else 'FAIL'}")
    print(f"  {google_msg}")
    if settings.credentials_path.exists():
        print(f"  client: {settings.credentials_path}")
    if settings.token_path.exists():
        print(f"  token:  {settings.token_path}")
    if not google_ok:
        print("  Fix: python -m syncer reauth-google")
        print(
            "  Note: OAuth apps left in Testing expire refresh tokens after ~7 days."
        )
    print()

    if exchange_ok and google_ok:
        print("Both look good. Run: python -m syncer sync")
    else:
        raise SystemExit(1)


def cmd_check() -> None:
    settings = load_settings()
    print(f"config: {settings.config_path}")
    print(f"source: {settings.source}")
    if not settings.credentials_path.exists():
        raise SystemExit(
            "Missing credentials.json. Run: python -m syncer setup --google-only"
        )
    print(f"google oauth client: {settings.credentials_path}")
    if settings.source == "ews":
        from . import ews

        assert settings.ews is not None
        account = ews.connect(settings.ews)
        print(f"exchange: {account.primary_smtp_address} on {settings.ews.server}")
    else:
        from . import apple

        store = apple.connect_store()
        apple.resolve_calendar(store, settings.apple_calendar)
        print(f"apple calendar: {settings.apple_calendar}")
    google_service(settings.credentials_path, settings.token_path)
    print("google login: ok")
    print("Ready. Run: python -m syncer sync")


def _print_menu() -> None:
    print(
        dedent(
            """\
            outlook-to-gmail-calendar-syncer
            ================================

            Enter the number of an option (for example: 9 for sync).
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
    if args.command == "setup":
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
    elif args.command == "sync":
        sync(load_settings(), dry_run=args.dry_run)
    elif args.command == "install-schedule":
        install_schedule()
    elif args.command == "uninstall-schedule":
        uninstall_schedule()
    else:
        raise SystemExit(f"Unknown command: {args.command}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m syncer",
        description=(
            "Copy Outlook/Exchange events into Google Calendar. "
            "Run with no arguments for an interactive menu, or `python -m syncer setup` first."
        ),
    )
    sub = parser.add_subparsers(dest="command")

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
