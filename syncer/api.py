from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from .config import ConfigError, Settings, load_settings
from .google import (
    check_google_token,
    clear_google_token,
    detect_timezone,
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
    dry_run: bool = False,
    log: LogFn | None = None,
    cancel: CancelEvent | None = None,
) -> SyncResult:
    try:
        settings = settings or load_settings()
    except ConfigError as exc:
        _log(log, "error", str(exc))
        return SyncResult(ok=False, message=str(exc), dry_run=dry_run)

    window_start, window_end = default_window(settings.days_back, settings.days_forward)
    try:
        if events is None:
            get = get_events(settings, log=log, cancel=cancel)
            if not get.ok:
                return SyncResult(ok=False, message=get.message, dry_run=dry_run)
            events = get.events
            if get.window_start and get.window_end:
                window_start, window_end = get.window_start, get.window_end

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
            window_start=window_start,
            window_end=window_end,
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
            _log(log, "info", "Password saved in macOS Keychain.")
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


def format_event_row(event: SourceEvent, privacy: str, timezone: str = "") -> str:
    tz = detect_timezone(timezone)
    title = "Busy" if privacy == "busy" else event.title
    when = event.start.astimezone(tz).strftime("%Y-%m-%d %H:%M")
    end = event.end.astimezone(tz).strftime("%H:%M")
    loc = f" @ {event.location}" if event.location and privacy != "busy" else ""
    return f"{when}–{end}  {title}{loc}"
