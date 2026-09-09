from __future__ import annotations

import argparse
import sys

from .config import load_settings
from .google import google_service
from .schedule import install_schedule, uninstall_schedule
from .sync import sync


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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m syncer",
        description="Copy Outlook/Exchange events into Google Calendar. Run `python -m syncer setup` first.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("login", help="Save Exchange password in Keychain and test the login.")
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

    args = parser.parse_args(argv)
    if args.command == "setup":
        from .wizard import run_wizard

        run_wizard(google_only=args.google_only)
    elif args.command == "login":
        cmd_login()
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
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
