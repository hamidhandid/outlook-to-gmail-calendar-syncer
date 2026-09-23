from __future__ import annotations

import hashlib
import threading
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from .config import Settings
from .google import (
    delete_event,
    detect_timezone,
    event_body,
    list_synced_events,
    upsert_event,
)
from .models import SourceEvent

LogFn = Callable[[str, str], None]
CancelEvent = threading.Event


class Cancelled(Exception):
    """Raised when the user asks to stop a Get/Sync."""


def _emit(log: LogFn | None, level: str, message: str) -> None:
    if log:
        log(level, message)
    else:
        print(message)


def check_cancelled(cancel: CancelEvent | None) -> None:
    if cancel is not None and cancel.is_set():
        raise Cancelled("Cancelled by user")


def fingerprint(title: str, location: str, notes: str, start: str, end: str, extra: str) -> str:
    payload = "|".join([title, location, notes, start, end, extra])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def _google_start(event: dict, tz: ZoneInfo) -> datetime | None:
    start = event.get("start") or {}
    if start.get("dateTime"):
        return datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
    if start.get("date"):
        return datetime.fromisoformat(start["date"]).replace(tzinfo=tz)
    return None


def load_source_events(
    settings: Settings,
    start: datetime,
    end: datetime,
    *,
    log: LogFn | None = None,
    cancel: CancelEvent | None = None,
) -> list[SourceEvent]:
    check_cancelled(cancel)
    if settings.source == "ews":
        from . import ews

        assert settings.ews is not None
        _emit(
            log,
            "info",
            f"Reading Exchange {settings.ews.email} on {settings.ews.server} "
            f"from {start.date()} to {end.date()}…",
        )
        events = ews.load_events(
            settings.ews,
            start,
            end,
            include_notes=settings.privacy == "full",
        )
        check_cancelled(cancel)
        return events
    from . import apple

    _emit(
        log,
        "info",
        f"Reading Apple Calendar {settings.apple_calendar!r} "
        f"from {start.date()} to {end.date()}…",
    )
    events = apple.load_events(settings.apple_calendar, start, end)
    check_cancelled(cancel)
    return events


def list_existing_by_origin(service: Any, calendar_id: str) -> dict[str, dict]:
    existing = list_synced_events(service, calendar_id)
    by_origin: dict[str, dict] = {}
    for item in existing:
        origin = (item.get("extendedProperties") or {}).get("private", {}).get("origin_id")
        if origin:
            by_origin[origin] = item
    return by_origin


def push_events_to_google(
    settings: Settings,
    source_events: list[SourceEvent],
    *,
    service: Any,
    calendar_id: str,
    by_origin: dict[str, dict],
    window_start: datetime,
    window_end: datetime,
    tz: ZoneInfo,
    dry_run: bool = False,
    log: LogFn | None = None,
    cancel: CancelEvent | None = None,
) -> dict[str, int]:
    created = updated = skipped = 0
    seen: set[str] = set()
    for event in source_events:
        check_cancelled(cancel)
        seen.add(event.origin_id)
        title = "Busy" if settings.privacy == "busy" else event.title
        location = "" if settings.privacy == "busy" else event.location
        notes = "" if settings.privacy == "busy" else event.notes
        fp = fingerprint(
            title,
            location,
            notes,
            event.start.isoformat(),
            event.end.isoformat(),
            f"{event.all_day}|{event.busy}|{event.tentative}|{settings.privacy}",
        )
        current = by_origin.get(event.origin_id)
        current_fp = (
            (current.get("extendedProperties") or {}).get("private", {}).get("fp")
            if current
            else None
        )
        if current and current_fp == fp:
            skipped += 1
            continue
        body = event_body(event, settings.privacy, tz, fp)
        action = "update" if current else "create"
        _emit(
            log,
            "info",
            f"  {action:6}  {event.start.astimezone(tz):%Y-%m-%d %H:%M}  {title}",
        )
        if dry_run:
            if current:
                updated += 1
            else:
                created += 1
            continue
        result = upsert_event(service, calendar_id, body, current)
        if result == "created":
            created += 1
        else:
            updated += 1

    deleted = 0
    for origin, item in by_origin.items():
        check_cancelled(cancel)
        if origin in seen:
            continue
        start = _google_start(item, tz)
        if start is None:
            continue
        if (
            start.astimezone(timezone.utc) < window_start
            or start.astimezone(timezone.utc) > window_end
        ):
            continue
        _emit(log, "info", f"  delete  {item.get('summary')}")
        if not dry_run:
            delete_event(service, calendar_id, item["id"])
        deleted += 1

    return {
        "created": created,
        "updated": updated,
        "deleted": deleted,
        "unchanged": skipped,
    }
