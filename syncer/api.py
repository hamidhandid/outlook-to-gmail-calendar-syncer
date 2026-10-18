from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .config import ConfigError, Settings, load_settings
from .bootstrap import CREDENTIALS_PLACEHOLDER_PATH, CREDENTIALS_PATH, TOKEN_PATH
from .encrypted_store import (
    default_store_path,
    load_encrypted_events,
    save_encrypted_events,
)
from .google import (
    check_google_token,
    clear_google_token,
    delete_calendar,
    detect_timezone,
    find_calendar_by_name,
    find_or_create_calendar,
    google_service,
)
from .models import SourceEvent, default_window
from .sync import (
    CancelEvent,
    Cancelled,
    list_existing_by_origin,
    load_source_events,
    push_events_to_google,
)

LogFn = Callable[[str, str], None]  # (level, message) level in {info, success, error}


def _log(log: LogFn | None, level: str, message: str) -> None:
    if log:
        log(level, message)
    else:
        print(message)


@dataclass
class GetResult:
    ok: bool
    events: list[SourceEvent] = field(default_factory=list)
    message: str = ""
    window_start: datetime | None = None
    window_end: datetime | None = None


@dataclass
class SyncResult:
    ok: bool
    message: str = ""
    created: int = 0
    updated: int = 0
    deleted: int = 0
    unchanged: int = 0
    dry_run: bool = False


@dataclass
class StoreResult:
    ok: bool
    message: str = ""
    path: Path | None = None
    count: int = 0


@dataclass
class TokensResult:
    ok: bool
    exchange_ok: bool
    google_ok: bool
    exchange_message: str = ""
    google_message: str = ""
    message: str = ""


def require_settings() -> Settings:
    try:
        return load_settings()
    except ConfigError as exc:
        raise SystemExit(str(exc)) from exc


def get_events(
    settings: Settings | None = None,
    *,
    log: LogFn | None = None,
    cancel: CancelEvent | None = None,
) -> GetResult:
    try:
        settings = settings or load_settings()
    except ConfigError as exc:
        _log(log, "error", str(exc))
        return GetResult(ok=False, message=str(exc))

    window_start, window_end = default_window(settings.days_back, settings.days_forward)
    try:
        events = load_source_events(
            settings, window_start, window_end, log=log, cancel=cancel
        )
    except Cancelled as exc:
        msg = str(exc)
        _log(log, "error", msg)
        return GetResult(ok=False, message=msg)
    except SystemExit as exc:
        msg = str(exc.code) if isinstance(exc.code, str) else str(exc)
        _log(log, "error", msg)
        return GetResult(ok=False, message=msg)
    except Exception as exc:
        msg = f"Failed to read Outlook/Exchange: {exc}"
        _log(log, "error", msg)
        return GetResult(ok=False, message=msg)

    msg = (
        f"Found {len(events)} event(s) from {window_start.date()} to {window_end.date()}"
    )
    _log(log, "success", msg)
    return GetResult(
        ok=True,
        events=events,
        message=msg,
        window_start=window_start,
        window_end=window_end,
    )


def run_sync(
    settings: Settings | None = None,
    *,
    events: list[SourceEvent] | None = None,
    window_start: datetime | None = None,
    window_end: datetime | None = None,
    dry_run: bool = False,
    log: LogFn | None = None,
    cancel: CancelEvent | None = None,
) -> SyncResult:
    try:
        settings = settings or load_settings()
    except ConfigError as exc:
        _log(log, "error", str(exc))
        return SyncResult(ok=False, message=str(exc), dry_run=dry_run)

    default_start, default_end = default_window(settings.days_back, settings.days_forward)
    sync_start = window_start or default_start
    sync_end = window_end or default_end
    try:
        if events is None:
            get = get_events(settings, log=log, cancel=cancel)
            if not get.ok:
                return SyncResult(ok=False, message=get.message, dry_run=dry_run)
            events = get.events
            if get.window_start and get.window_end:
                sync_start, sync_end = get.window_start, get.window_end

        tz = detect_timezone(settings.timezone)
        _log(log, "info", "Connecting to Google Calendar…")
        if cancel is not None and cancel.is_set():
            raise Cancelled("Cancelled by user")
        service = google_service(settings.credentials_path, settings.token_path)
        _log(log, "info", "Looking up / creating the Google calendar…")
        if cancel is not None and cancel.is_set():
            raise Cancelled("Cancelled by user")
        calendar_id = find_or_create_calendar(
            service, settings.google_calendar, str(tz)
        )
        _log(
            log,
            "info",
            f"Google calendar: {settings.google_calendar} ({calendar_id})",
        )
        _log(log, "info", "Loading previously synced Google events…")
        if cancel is not None and cancel.is_set():
            raise Cancelled("Cancelled by user")
        by_origin = list_existing_by_origin(service, calendar_id)
        _log(log, "info", f"Already mirrored on Google: {len(by_origin)}")

        counts = push_events_to_google(
            settings,
            events,
            service=service,
            calendar_id=calendar_id,
            by_origin=by_origin,
            window_start=sync_start,
            window_end=sync_end,
            tz=tz,
            dry_run=dry_run,
            log=log,
            cancel=cancel,
        )
    except Cancelled as exc:
        msg = str(exc)
        _log(log, "error", msg)
        return SyncResult(ok=False, message=msg, dry_run=dry_run)
    except SystemExit as exc:
        msg = str(exc.code) if isinstance(exc.code, str) else str(exc)
        _log(log, "error", msg)
        return SyncResult(ok=False, message=msg, dry_run=dry_run)
    except Exception as exc:
        msg = f"Sync failed: {exc}"
        _log(log, "error", msg)
        return SyncResult(ok=False, message=msg, dry_run=dry_run)

    prefix = "Dry run. Would have " if dry_run else ""
    summary = (
        f"{prefix}created={counts['created']} updated={counts['updated']} "
        f"deleted={counts['deleted']} unchanged={counts['unchanged']}"
    )
    _log(log, "success", summary)
    if not events:
        hint = (
            "No source events. Connect the company VPN and confirm OWA shows meetings."
            if settings.source == "ews"
            else "No source events. Confirm Calendar.app shows the work calendar."
        )
        _log(log, "info", hint)
    return SyncResult(
        ok=True,
        message=summary,
        created=counts["created"],
        updated=counts["updated"],
        deleted=counts["deleted"],
        unchanged=counts["unchanged"],
        dry_run=dry_run,
    )


def store_events_encrypted(
    settings: Settings | None = None,
    *,
    path: Path | None = None,
    password: str | None = None,
    log: LogFn | None = None,
    cancel: CancelEvent | None = None,
) -> StoreResult:
    """Fetch Outlook/Exchange events and write them to a password-encrypted file."""
    try:
        settings = settings or load_settings()
    except ConfigError as exc:
        _log(log, "error", str(exc))
        return StoreResult(ok=False, message=str(exc))

    get = get_events(settings, log=log, cancel=cancel)
    if not get.ok:
        return StoreResult(ok=False, message=get.message)
    assert get.window_start is not None and get.window_end is not None

    target = path or default_store_path()
    try:
        saved = save_encrypted_events(
            get.events,
            path=target,
            privacy=settings.privacy,
            window_start=get.window_start,
            window_end=get.window_end,
            password=password,
        )
    except SystemExit as exc:
        msg = str(exc.code) if isinstance(exc.code, str) else str(exc)
        _log(log, "error", msg)
        return StoreResult(ok=False, message=msg)
    except Exception as exc:
        msg = f"Failed to write encrypted events file: {exc}"
        _log(log, "error", msg)
        return StoreResult(ok=False, message=msg)

    msg = (
        f"Saved {len(get.events)} event(s) encrypted to {saved}\n"
        f"Window: {get.window_start.date()} → {get.window_end.date()}\n"
        "Later (no company VPN needed for Outlook): python -m syncer sync-stored"
    )
    _log(log, "success", msg)
    return StoreResult(ok=True, message=msg, path=saved, count=len(get.events))


def run_sync_from_encrypted(
    settings: Settings | None = None,
    *,
    path: Path | None = None,
    password: str | None = None,
    dry_run: bool = False,
    log: LogFn | None = None,
    cancel: CancelEvent | None = None,
) -> SyncResult:
    """Decrypt a previously stored events file and sync it to Google Calendar."""
    try:
        settings = settings or load_settings()
    except ConfigError as exc:
        _log(log, "error", str(exc))
        return SyncResult(ok=False, message=str(exc), dry_run=dry_run)

    source = path or default_store_path()
    try:
        bundle = load_encrypted_events(source, password=password)
    except SystemExit as exc:
        msg = str(exc.code) if isinstance(exc.code, str) else str(exc)
        _log(log, "error", msg)
        return SyncResult(ok=False, message=msg, dry_run=dry_run)
    except Exception as exc:
        msg = f"Failed to read encrypted events file: {exc}"
        _log(log, "error", msg)
        return SyncResult(ok=False, message=msg, dry_run=dry_run)

    _log(
        log,
        "info",
        f"Loaded {len(bundle.events)} event(s) from {bundle.path} "
        f"(saved {bundle.created_at.isoformat(timespec='seconds')}, "
        f"window {bundle.window_start.date()} → {bundle.window_end.date()})",
    )
    return run_sync(
        settings,
        events=bundle.events,
        window_start=bundle.window_start,
        window_end=bundle.window_end,
        dry_run=dry_run,
        log=log,
        cancel=cancel,
    )


def check_tokens_status(
    settings: Settings | None = None,
    *,
    log: LogFn | None = None,
) -> TokensResult:
    try:
        settings = settings or load_settings()
    except ConfigError as exc:
        _log(log, "error", str(exc))
        return TokensResult(
            ok=False,
            exchange_ok=False,
            google_ok=False,
            message=str(exc),
        )

    exchange_ok = True
    exchange_msg = f"source={settings.source} (no Exchange password required)"
    if settings.source == "ews" and settings.ews is not None:
        from . import ews

        try:
            ews.password_for(settings.ews.email)
            account = ews.connect(settings.ews)
            exchange_msg = (
                f"ok ({account.primary_smtp_address} on {settings.ews.server})"
            )
        except SystemExit as exc:
            exchange_ok = False
            exchange_msg = str(exc.code) if isinstance(exc.code, str) else str(exc)
        except Exception as exc:
            exchange_ok = False
            exchange_msg = str(exc)

    google_ok, google_msg = check_google_token(
        settings.credentials_path, settings.token_path
    )
    _log(log, "success" if exchange_ok else "error", f"Exchange: {exchange_msg}")
    _log(log, "success" if google_ok else "error", f"Google: {google_msg}")
    ok = exchange_ok and google_ok
    message = "Both look good." if ok else "Fix Exchange and/or Google login."
    _log(log, "success" if ok else "error", message)
    return TokensResult(
        ok=ok,
        exchange_ok=exchange_ok,
        google_ok=google_ok,
        exchange_message=exchange_msg,
        google_message=google_msg,
        message=message,
    )


def login_exchange(
    settings: Settings | None = None,
    *,
    password: str | None = None,
    log: LogFn | None = None,
) -> tuple[bool, str]:
    try:
        settings = settings or load_settings()
    except ConfigError as exc:
        _log(log, "error", str(exc))
        return False, str(exc)
    if settings.source != "ews" or settings.ews is None:
        msg = "login is only used with source: ews"
        _log(log, "error", msg)
        return False, msg
    from . import ews

    try:
        if password:
            ews.save_password(settings.ews.email, password)
            from .platform_util import keyring_store_name

            _log(log, "info", f"Password saved in {keyring_store_name()}.")
        else:
            ews.prompt_and_save_password(settings.ews.email)
        account = ews.connect(settings.ews)
        msg = f"Connected to {settings.ews.server} as {account.primary_smtp_address}"
        _log(log, "success", msg)
        return True, msg
    except SystemExit as exc:
        msg = str(exc.code) if isinstance(exc.code, str) else str(exc)
        _log(log, "error", msg)
        return False, msg
    except Exception as exc:
        msg = str(exc)
        _log(log, "error", msg)
        return False, msg


def reauth_google(
    settings: Settings | None = None,
    *,
    log: LogFn | None = None,
) -> tuple[bool, str]:
    try:
        settings = settings or load_settings()
    except ConfigError as exc:
        _log(log, "error", str(exc))
        return False, str(exc)
    if not settings.credentials_path.exists():
        msg = "Missing credentials.json. Run: python -m syncer setup --google-only"
        _log(log, "error", msg)
        return False, msg
    try:
        if clear_google_token(settings.token_path):
            _log(log, "info", f"Removed old token: {settings.token_path}")
        google_service(
            settings.credentials_path, settings.token_path, force_reauth=True
        )
        msg = "Google login: ok"
        _log(log, "success", msg)
        return True, msg
    except SystemExit as exc:
        msg = str(exc.code) if isinstance(exc.code, str) else str(exc)
        _log(log, "error", msg)
        return False, msg
    except Exception as exc:
        msg = str(exc)
        _log(log, "error", msg)
        return False, msg


def check_outlook_auth(
    settings: Settings | None = None,
    *,
    log: LogFn | None = None,
) -> tuple[bool, str]:
    """Test Exchange / Outlook login only."""
    try:
        settings = settings or load_settings()
    except ConfigError as exc:
        _log(log, "error", str(exc))
        return False, str(exc)
    if settings.source != "ews" or settings.ews is None:
        msg = "Outlook auth check needs source: ews"
        _log(log, "error", msg)
        return False, msg
    from . import ews

    try:
        account = ews.connect(settings.ews)
        msg = f"Connected to {settings.ews.server} as {account.primary_smtp_address}"
        _log(log, "success", msg)
        return True, msg
    except SystemExit as exc:
        msg = str(exc.code) if isinstance(exc.code, str) else str(exc)
        _log(log, "error", msg)
        return False, msg
    except Exception as exc:
        msg = str(exc)
        _log(log, "error", msg)
        return False, msg


def check_google_auth(
    settings: Settings | None = None,
    *,
    log: LogFn | None = None,
) -> tuple[bool, str]:
    """Test Google OAuth token only."""
    try:
        settings = settings or load_settings()
    except ConfigError as exc:
        _log(log, "error", str(exc))
        return False, str(exc)
    ok, msg = check_google_token(settings.credentials_path, settings.token_path)
    _log(log, "success" if ok else "error", msg)
    return ok, msg


def remove_google_credentials(
    settings: Settings | None = None,
    *,
    confirmed: bool = False,
    log: LogFn | None = None,
) -> tuple[bool, str]:
    """Remove credentials.json and token.json. Does not delete the Google Calendar."""
    if not confirmed:
        msg = "Remove cancelled: confirmation required."
        _log(log, "error", msg)
        return False, msg
    try:
        settings = settings or load_settings()
        token_path = settings.token_path
        creds_path = settings.credentials_path
    except ConfigError:
        token_path = TOKEN_PATH
        creds_path = CREDENTIALS_PATH

    steps: list[str] = []
    for path, label in (
        (token_path, "token.json"),
        (creds_path, "credentials.json"),
        (CREDENTIALS_PLACEHOLDER_PATH, "credentials.PLACEHOLDER.json"),
    ):
        try:
            if path.exists():
                path.unlink()
                steps.append(f"Removed {label}")
                _log(log, "success", steps[-1])
            else:
                steps.append(f"{label}: already absent")
        except OSError as exc:
            steps.append(f"Could not remove {label}: {exc}")
            _log(log, "error", steps[-1])
    summary = "Google credentials removed.\n" + "\n".join(f"  • {s}" for s in steps)
    return True, summary


def format_event_row(event: SourceEvent, privacy: str, timezone: str = "") -> str:
    tz = detect_timezone(timezone)
    title = "Busy" if privacy == "busy" else event.title
    when = event.start.astimezone(tz).strftime("%Y-%m-%d %H:%M")
    end = event.end.astimezone(tz).strftime("%H:%M")
    loc = f" @ {event.location}" if event.location and privacy != "busy" else ""
    return f"{when}–{end}  {title}{loc}"


@dataclass
class ResetResult:
    ok: bool
    message: str = ""
    steps: list[str] = field(default_factory=list)


def reset_credentials_and_calendar(
    settings: Settings | None = None,
    *,
    delete_google_calendar: bool = True,
    confirmed: bool = False,
    log: LogFn | None = None,
) -> ResetResult:
    """Remove Google sync calendar (optional), OAuth files, encrypted store, Exchange password.

    Does **not** delete config.yaml. Requires confirmed=True (caller must warn the user).
    """
    if not confirmed:
        msg = "Reset cancelled: confirmation required."
        _log(log, "error", msg)
        return ResetResult(ok=False, message=msg)

    steps: list[str] = []
    try:
        settings = settings or load_settings()
    except ConfigError:
        settings = None

    # 1) Delete the dedicated Google calendar if we can authenticate.
    if delete_google_calendar and settings is not None:
        cal_name = settings.google_calendar
        if settings.credentials_path.exists() and settings.token_path.exists():
            try:
                _log(log, "info", f"Looking up Google calendar {cal_name!r} to delete…")
                service = google_service(settings.credentials_path, settings.token_path)
                found = find_calendar_by_name(service, cal_name)
                if found is None:
                    steps.append(f"Google calendar {cal_name!r}: not found (skipped)")
                elif found.get("primary"):
                    steps.append(
                        f"Google calendar {cal_name!r}: is primary — not deleted"
                    )
                else:
                    delete_calendar(service, found["id"])
                    steps.append(f"Deleted Google calendar {cal_name!r} ({found['id']})")
                    _log(log, "success", steps[-1])
            except SystemExit as exc:
                detail = str(exc.code) if isinstance(exc.code, str) else str(exc)
                steps.append(f"Google calendar delete skipped: {detail}")
                _log(log, "error", steps[-1])
            except Exception as exc:
                steps.append(f"Google calendar delete skipped: {exc}")
                _log(log, "error", steps[-1])
        else:
            steps.append(
                "Google calendar delete skipped (no credentials.json / token.json yet)"
            )
            _log(log, "info", steps[-1])

    # 2) Local Google OAuth files
    for path, label in (
        (TOKEN_PATH if settings is None else settings.token_path, "token.json"),
        (
            CREDENTIALS_PATH if settings is None else settings.credentials_path,
            "credentials.json",
        ),
        (CREDENTIALS_PLACEHOLDER_PATH, "credentials.PLACEHOLDER.json"),
    ):
        try:
            if path.exists():
                path.unlink()
                steps.append(f"Removed {label}")
                _log(log, "success", steps[-1])
            else:
                steps.append(f"{label}: already absent")
        except OSError as exc:
            steps.append(f"Could not remove {label}: {exc}")
            _log(log, "error", steps[-1])

    # 3) Encrypted events store
    store = default_store_path()
    try:
        if store.exists():
            store.unlink()
            steps.append(f"Removed {store.name}")
            _log(log, "success", steps[-1])
        else:
            steps.append(f"{store.name}: already absent")
    except OSError as exc:
        steps.append(f"Could not remove {store.name}: {exc}")
        _log(log, "error", steps[-1])

    # 4) Exchange password in OS keyring
    email = ""
    if settings is not None and settings.ews is not None:
        email = settings.ews.email
    if email:
        from . import ews

        if ews.clear_password(email):
            steps.append(f"Removed Exchange password for {email} from the keyring")
            _log(log, "success", steps[-1])
        else:
            steps.append(f"No Exchange password found in the keyring for {email}")
            _log(log, "info", steps[-1])
    else:
        steps.append("Exchange password: skipped (no email in config)")
        _log(log, "info", steps[-1])

    summary = "Reset finished.\n" + "\n".join(f"  • {s}" for s in steps)
    _log(log, "success", "Reset finished.")
    return ResetResult(ok=True, message=summary, steps=steps)
