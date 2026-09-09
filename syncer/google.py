from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import SYNC_SOURCE, SourceEvent

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def google_service(credentials_path: Path, token_path: Path) -> Any:
    if not credentials_path.exists():
        raise SystemExit(
            f"Missing {credentials_path.name}. Download the Desktop OAuth client JSON\n"
            "from Google Cloud Console and save it as credentials.json in this folder.\n"
            "See README.md for the exact clicks."
        )
    creds: Credentials | None = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json())
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _all_pages(request_fn) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page_token = None
    while True:
        result = request_fn(page_token)
        items.extend(result.get("items", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            return items


def find_or_create_calendar(service: Any, name: str, tz_name: str) -> str:
    calendars = _all_pages(
        lambda token: service.calendarList().list(pageToken=token).execute()
    )
    for item in calendars:
        if item.get("summary") == name:
            return item["id"]
    created = (
        service.calendars()
        .insert(body={"summary": name, "timeZone": tz_name})
        .execute()
    )
    return created["id"]


def list_synced_events(service: Any, calendar_id: str) -> list[dict[str, Any]]:
    return _all_pages(
        lambda token: service.events()
        .list(
            calendarId=calendar_id,
            privateExtendedProperty=f"sync_source={SYNC_SOURCE}",
            singleEvents=True,
            maxResults=2500,
            pageToken=token,
        )
        .execute()
    )


def _local_date(dt: datetime, tz: ZoneInfo) -> date:
    return dt.astimezone(tz).date()


def event_body(
    source: SourceEvent,
    privacy: str,
    tz: ZoneInfo,
    fingerprint: str,
) -> dict[str, Any]:
    if privacy == "busy":
        title = "Busy"
        location = ""
        notes = ""
    else:
        title = source.title
        location = source.location
        notes = source.notes

    body: dict[str, Any] = {
        "summary": title,
        "location": location,
        "description": notes,
        "status": "tentative" if source.tentative else "confirmed",
        "transparency": "opaque" if source.busy else "transparent",
        "guestsCanInviteOthers": False,
        "guestsCanModify": False,
        "extendedProperties": {
            "private": {
                "sync_source": SYNC_SOURCE,
                "origin_id": source.origin_id,
                "fp": fingerprint,
            }
        },
        "reminders": {"useDefault": True},
    }
    if source.all_day:
        start_d = _local_date(source.start, tz)
        end_d = _local_date(source.end, tz)
        if end_d <= start_d:
            end_d = start_d + timedelta(days=1)
        body["start"] = {"date": start_d.isoformat()}
        body["end"] = {"date": end_d.isoformat()}
    else:
        body["start"] = {
            "dateTime": source.start.astimezone(tz).isoformat(),
            "timeZone": str(tz),
        }
        body["end"] = {
            "dateTime": source.end.astimezone(tz).isoformat(),
            "timeZone": str(tz),
        }
    return body


def upsert_event(
    service: Any,
    calendar_id: str,
    body: dict[str, Any],
    existing: dict[str, Any] | None,
) -> str:
    try:
        if existing:
            service.events().update(
                calendarId=calendar_id,
                eventId=existing["id"],
                body=body,
                sendUpdates="none",
            ).execute()
            return "updated"
        service.events().insert(
            calendarId=calendar_id,
            body=body,
            sendUpdates="none",
        ).execute()
        return "created"
    except HttpError as exc:
        raise SystemExit(f"Google Calendar API error: {exc}") from exc


def delete_event(service: Any, calendar_id: str, event_id: str) -> None:
    try:
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id,
            sendUpdates="none",
        ).execute()
    except HttpError as exc:
        if exc.resp.status == 410:
            return
        raise SystemExit(f"Google Calendar API error: {exc}") from exc


def detect_timezone(configured: str) -> ZoneInfo:
    if configured:
        return ZoneInfo(configured)
    from Foundation import NSTimeZone  # type: ignore

    return ZoneInfo(str(NSTimeZone.localTimeZone().name()))
