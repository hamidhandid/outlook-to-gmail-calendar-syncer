from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from google.auth.exceptions import RefreshError, TransportError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import SSLError, Timeout

from .models import SYNC_SOURCE, SourceEvent

SCOPES = ["https://www.googleapis.com/auth/calendar"]
GOOGLE_HTTP_TIMEOUT = 30  # seconds — fail fast when the VPN blocks Google

_NETWORK_HINT = (
    "Could not reach Google (oauth2.googleapis.com / googleapis.com).\n"
    "This usually means the company VPN is blocking or breaking HTTPS to Google.\n"
    "\n"
    "Try one of these:\n"
    "  1. Briefly disconnect the VPN, run: python -m syncer reauth-google\n"
    "     (or sync again), then reconnect the VPN for Exchange.\n"
    "  2. Ask IT for split tunneling so Google stays on the public internet.\n"
    "  3. Confirm a browser can open https://oauth2.googleapis.com\n"
)


class _TimedRequest(Request):
    """google-auth Request with a short timeout so VPN hangs fail fast."""

    def __call__(self, *args: Any, **kwargs: Any):  # type: ignore[override]
        kwargs.setdefault("timeout", GOOGLE_HTTP_TIMEOUT)
        return super().__call__(*args, **kwargs)


def _google_network_error(exc: BaseException) -> SystemExit:
    detail = str(exc) or type(exc).__name__
    if "timed out" in detail.lower() or "timeout" in detail.lower():
        return SystemExit(
            f"{_NETWORK_HINT}\n"
            f"Timed out after {GOOGLE_HTTP_TIMEOUT}s talking to Google.\n"
            f"Detail: {detail}"
        )
    return SystemExit(f"{_NETWORK_HINT}\nDetail: {detail}")


def clear_google_token(token_path: Path) -> bool:
    if token_path.exists():
        token_path.unlink()
        return True
    return False


def _browser_login(credentials_path: Path, token_path: Path) -> Credentials:
    print("Opening a browser to sign in to Google Calendar…")
    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)
    except (TransportError, SSLError, RequestsConnectionError, Timeout, OSError) as exc:
        raise _google_network_error(exc) from exc
    token_path.write_text(creds.to_json())
    print(f"Saved Google token: {token_path}")
    return creds


def load_google_credentials(
    credentials_path: Path,
    token_path: Path,
    *,
    force_reauth: bool = False,
) -> Credentials:
    if not credentials_path.exists():
        raise SystemExit(
            f"Missing {credentials_path.name}. Download the Desktop OAuth client JSON\n"
            "from Google Cloud Console and save it as credentials.json in this folder.\n"
            "Run: python -m syncer setup --google-only"
        )
    if force_reauth:
        clear_google_token(token_path)
        return _browser_login(credentials_path, token_path)

    creds: Credentials | None = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        print(
            f"Refreshing Google access token (timeout {GOOGLE_HTTP_TIMEOUT}s)…"
        )
        try:
            creds.refresh(_TimedRequest())
            token_path.write_text(creds.to_json())
            return creds
        except RefreshError:
            print(
                "Google refresh token expired or was revoked "
                "(common while the OAuth app is in Testing — tokens last ~7 days).\n"
                "Signing in again…"
            )
            clear_google_token(token_path)
            return _browser_login(credentials_path, token_path)
        except (TransportError, SSLError, RequestsConnectionError, Timeout, OSError) as exc:
            raise _google_network_error(exc) from exc

    return _browser_login(credentials_path, token_path)


def google_service(
    credentials_path: Path,
    token_path: Path,
    *,
    force_reauth: bool = False,
) -> Any:
    import httplib2
    from google_auth_httplib2 import AuthorizedHttp

    creds = load_google_credentials(
        credentials_path, token_path, force_reauth=force_reauth
    )
    http = AuthorizedHttp(creds, http=httplib2.Http(timeout=GOOGLE_HTTP_TIMEOUT))
    return build("calendar", "v3", http=http, cache_discovery=False)


def check_google_token(credentials_path: Path, token_path: Path) -> tuple[bool, str]:
    if not credentials_path.exists():
        return False, "missing credentials.json — run: python -m syncer setup --google-only"
    if not token_path.exists():
        return False, "no token.json yet — run: python -m syncer reauth-google"
    try:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    except Exception as exc:
        return False, f"token.json unreadable ({exc}) — run: python -m syncer reauth-google"
    if not creds.refresh_token and not creds.valid:
        return False, "token has no refresh_token — run: python -m syncer reauth-google"
    if creds.valid:
        return True, "valid"
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(_TimedRequest())
            token_path.write_text(creds.to_json())
            return True, "expired access token refreshed successfully"
        except RefreshError:
            return (
                False,
                "refresh token expired/revoked — run: python -m syncer reauth-google",
            )
        except (TransportError, SSLError, RequestsConnectionError, Timeout, OSError) as exc:
            return (
                False,
                "cannot reach Google right now (often the company VPN). "
                f"Try without VPN, then: python -m syncer reauth-google — ({exc})",
            )
    return False, "token invalid — run: python -m syncer reauth-google"


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
    try:
        calendars = _all_pages(
            lambda token: service.calendarList().list(pageToken=token).execute()
        )
    except HttpError:
        raise
    except Exception as exc:
        raise _google_network_error(exc) from exc
    for item in calendars:
        if item.get("summary") == name:
            return item["id"]
    try:
        created = (
            service.calendars()
            .insert(body={"summary": name, "timeZone": tz_name})
            .execute()
        )
    except HttpError:
        raise
    except Exception as exc:
        raise _google_network_error(exc) from exc
    return created["id"]


def list_synced_events(service: Any, calendar_id: str) -> list[dict[str, Any]]:
    try:
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
    except HttpError:
        raise
    except Exception as exc:
        raise _google_network_error(exc) from exc


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
