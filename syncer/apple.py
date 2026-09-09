from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from EventKit import (  # type: ignore
    EKAuthorizationStatusDenied,
    EKAuthorizationStatusRestricted,
    EKEntityTypeEvent,
    EKEventStatusCanceled,
    EKEventStore,
)
from Foundation import NSDate, NSRunLoop  # type: ignore

from .models import CalendarInfo, SourceEvent


def _runloop_wait(done: list[bool], seconds: float = 30) -> None:
    deadline = time.time() + seconds
    while not done[0] and time.time() < deadline:
        NSRunLoop.currentRunLoop().runUntilDate_(
            NSDate.dateWithTimeIntervalSinceNow_(0.05)
        )


def _nsdate_to_datetime(nsdate: Any) -> datetime:
    return datetime.fromtimestamp(nsdate.timeIntervalSince1970(), tz=timezone.utc)


def _request_calendar_access(store: Any) -> None:
    status = int(EKEventStore.authorizationStatusForEntityType_(EKEntityTypeEvent))
    # 3 = authorized (older macOS), 5 = full access (Sonoma+)
    if status in (3, 5):
        return
    if status in (
        int(EKAuthorizationStatusDenied),
        int(EKAuthorizationStatusRestricted),
    ):
        raise SystemExit(
            "Calendar access is denied. Enable it in\n"
            "System Settings → Privacy & Security → Calendars\n"
            "for Terminal, Cursor, and Python, then retry."
        )

    done = [False]
    granted = [False]
    error_box: list[Any] = [None]

    def callback(ok: bool, error: Any) -> None:
        granted[0] = bool(ok)
        error_box[0] = error
        done[0] = True

    if hasattr(store, "requestFullAccessToEventsWithCompletion_"):
        store.requestFullAccessToEventsWithCompletion_(callback)
    else:
        store.requestAccessToEntityType_completion_(EKEntityTypeEvent, callback)

    _runloop_wait(done)
    if not done[0]:
        raise SystemExit(
            "Timed out waiting for Calendar permission. Grant access in\n"
            "System Settings → Privacy & Security → Calendars for Terminal, Cursor, and Python,\n"
            "then run this command again."
        )
    if not granted[0]:
        detail = f" ({error_box[0]})" if error_box[0] else ""
        raise SystemExit(
            "Calendar access was not granted"
            f"{detail}.\n"
            "System Settings → Privacy & Security → Calendars → enable this app\n"
            "(Terminal, Cursor, or Python), then retry."
        )


def connect_store() -> Any:
    store = EKEventStore.alloc().init()
    _request_calendar_access(store)
    return store


def list_calendars(store: Any | None = None) -> list[CalendarInfo]:
    store = store or connect_store()
    found: list[CalendarInfo] = []
    for calendar in store.calendarsForEntityType_(EKEntityTypeEvent) or []:
        source = calendar.source()
        account = str(source.title()) if source is not None else ""
        title = str(calendar.title() or "")
        label = f"{account} / {title}" if account else title
        found.append(
            CalendarInfo(
                identifier=str(calendar.calendarIdentifier()),
                title=title,
                account=account,
                label=label,
            )
        )
    found.sort(key=lambda item: item.label.lower())
    return found


def _matches(info: CalendarInfo, wanted: str) -> bool:
    wanted_l = wanted.lower()
    return wanted_l in {
        info.label.lower(),
        info.title.lower(),
        info.identifier.lower(),
    }


def resolve_calendar(store: Any, wanted: str) -> Any:
    matches: list[Any] = []
    matched_labels: list[str] = []
    for calendar in store.calendarsForEntityType_(EKEntityTypeEvent) or []:
        source = calendar.source()
        account = str(source.title()) if source is not None else ""
        title = str(calendar.title() or "")
        info = CalendarInfo(
            identifier=str(calendar.calendarIdentifier()),
            title=title,
            account=account,
            label=f"{account} / {title}" if account else title,
        )
        if _matches(info, wanted):
            matches.append(calendar)
            matched_labels.append(info.label)
    if len(matches) == 1:
        return matches[0]
    infos = list_calendars(store)
    if not matches:
        labels = "\n".join(f"  - {info.label}" for info in infos) or "  (none)"
        raise SystemExit(
            f"No Apple Calendar named {wanted!r}. Available calendars:\n{labels}\n"
            "Put one of those labels in config.yaml as apple_calendar."
        )
    labels = "\n".join(f"  - {name}" for name in matched_labels)
    raise SystemExit(
        f"{wanted!r} matches more than one calendar:\n{labels}\n"
        "Use the full 'Account / Calendar' label in config.yaml."
    )


def load_events(
    wanted_calendar: str,
    start: datetime,
    end: datetime,
    store: Any | None = None,
) -> list[SourceEvent]:
    store = store or connect_store()
    calendar = resolve_calendar(store, wanted_calendar)
    predicate = store.predicateForEventsWithStartDate_endDate_calendars_(
        NSDate.dateWithTimeIntervalSince1970_(start.timestamp()),
        NSDate.dateWithTimeIntervalSince1970_(end.timestamp()),
        [calendar],
    )
    raw = store.eventsMatchingPredicate_(predicate) or []
    events: list[SourceEvent] = []
    for event in raw:
        if int(event.status()) == int(EKEventStatusCanceled):
            continue
        start_dt = _nsdate_to_datetime(event.startDate())
        end_dt = _nsdate_to_datetime(event.endDate())
        all_day = bool(event.isAllDay())
        external = str(event.calendarItemExternalIdentifier() or "")
        identifier = str(event.eventIdentifier() or "")
        origin = external or identifier
        origin_id = f"{origin}|{start_dt.isoformat()}"
        availability = int(event.availability())
        # EKEventAvailabilityFree = 1
        busy = availability != 1
        tentative = int(event.status()) == 2  # EKEventStatusTentative
        events.append(
            SourceEvent(
                origin_id=origin_id,
                title=str(event.title() or "(No title)"),
                start=start_dt,
                end=end_dt,
                all_day=all_day,
                location=str(event.location() or ""),
                notes=str(event.notes() or "")[:8000],
                busy=busy,
                tentative=tentative,
            )
        )
    events.sort(key=lambda item: item.start)
    return events
