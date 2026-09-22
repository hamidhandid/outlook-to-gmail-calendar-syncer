from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .config import Settings
from .google import (
    delete_event,
    detect_timezone,
    event_body,
    find_or_create_calendar,
    google_service,
    list_synced_events,
    upsert_event,
)
from .models import SourceEvent, default_window


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


def load_source_events(settings: Settings, start: datetime, end: datetime) -> list[SourceEvent]:
    if settings.source == "ews":
        from . import ews

        assert settings.ews is not None
        print(
            f"Reading Exchange {settings.ews.email} on {settings.ews.server} "
            f"from {start.date()} to {end.date()}…"
        )
        return ews.load_events(
            settings.ews,
            start,
            end,
            include_notes=settings.privacy == "full",
        )
    from . import apple

    print(
        f"Reading Apple Calendar {settings.apple_calendar!r} "
        f"from {start.date()} to {end.date()}…"
    )
    return apple.load_events(settings.apple_calendar, start, end)


def sync(settings: Settings, dry_run: bool = False) -> None:
    tz = detect_timezone(settings.timezone)
    window_start, window_end = default_window(settings.days_back, settings.days_forward)
    source_events = load_source_events(settings, window_start, window_end)
    print(f"Found {len(source_events)} Outlook/Exchange event(s).")

    print("Connecting to Google Calendar…")
    service = google_service(settings.credentials_path, settings.token_path)
    print("Looking up / creating the Google calendar…")
    calendar_id = find_or_create_calendar(service, settings.google_calendar, str(tz))
    print(f"Google calendar: {settings.google_calendar} ({calendar_id})")

    print("Loading previously synced Google events…")
    existing = list_synced_events(service, calendar_id)
    by_origin: dict[str, dict] = {}
    for item in existing:
        origin = (item.get("extendedProperties") or {}).get("private", {}).get("origin_id")
        if origin:
            by_origin[origin] = item
    print(f"Already mirrored on Google: {len(by_origin)}")

    created = updated = skipped = 0
    seen: set[str] = set()
    for event in source_events:
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
        current_fp = (current.get("extendedProperties") or {}).get("private", {}).get("fp") if current else None
        if current and current_fp == fp:
            skipped += 1
            continue
        body = event_body(event, settings.privacy, tz, fp)
        action = "update" if current else "create"
        print(f"  {action:6}  {event.start.astimezone(tz):%Y-%m-%d %H:%M}  {title}")
        if dry_run:
            continue
        result = upsert_event(service, calendar_id, body, current)
        if result == "created":
            created += 1
        else:
            updated += 1

    deleted = 0
    for origin, item in by_origin.items():
        if origin in seen:
            continue
        start = _google_start(item, tz)
        if start is None:
            continue
        if start.astimezone(timezone.utc) < window_start or start.astimezone(timezone.utc) > window_end:
            continue
        print(f"  delete  {item.get('summary')}")
        if not dry_run:
            delete_event(service, calendar_id, item["id"])
        deleted += 1

    prefix = "Dry run. Would have " if dry_run else ""
    print(
        f"{prefix}created={created} updated={updated} deleted={deleted} unchanged={skipped}"
    )
    if not source_events:
        if settings.source == "ews":
            print(
                "No source events. Connect the company VPN, run `python -m syncer login`, "
                "and confirm OWA at mail.digikala.com shows meetings."
            )
        else:
            print(
                "No source events. Connect the company VPN, open Calendar.app, "
                "and confirm the work calendar is showing meetings, then retry."
            )
