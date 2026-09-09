from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

SYNC_SOURCE = "outlook-gmail-calendar-syncer"


@dataclass
class CalendarInfo:
    identifier: str
    title: str
    account: str
    label: str


@dataclass
class SourceEvent:
    origin_id: str
    title: str
    start: datetime
    end: datetime
    all_day: bool
    location: str
    notes: str
    busy: bool
    tentative: bool


def default_window(days_back: int, days_forward: int) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days_back)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = now + timedelta(days=days_forward)
    return start, end
