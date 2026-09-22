from __future__ import annotations

import getpass
import os
import warnings
from datetime import date, datetime, time, timezone
from typing import Any

import keyring
from urllib3.exceptions import InsecureRequestWarning
from exchangelib import (
    BASIC,
    DELEGATE,
    NTLM,
    Account,
    CalendarItem,
    Configuration,
    Credentials,
)
from exchangelib.errors import ErrorNonExistentMailbox, TransportError, UnauthorizedError
from exchangelib.folders import Calendar
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter

from .config import EwsSettings
from .models import CalendarInfo, SourceEvent

KEYRING_SERVICE = "outlook-to-gmail-calendar-syncer"
EWS_TIMEOUT_SECONDS = 45


def _auth_type(name: str) -> Any:
    if name == "basic":
        return BASIC
    if name == "ntlm":
        return NTLM
    raise SystemExit("config.yaml: ews.auth must be 'ntlm' or 'basic'")


def password_for(email: str) -> str:
    env = os.environ.get("EWS_PASSWORD", "").strip()
    if env:
        return env
    stored = keyring.get_password(KEYRING_SERVICE, email)
    if stored:
        return stored
    raise SystemExit(
        "No Exchange password saved. Connect the VPN, then run:\n"
        "  python -m syncer login\n"
        "Or set the EWS_PASSWORD environment variable."
    )


def save_password(email: str, password: str) -> None:
    keyring.set_password(KEYRING_SERVICE, email, password)


def prompt_and_save_password(email: str) -> str:
    password = getpass.getpass(f"Password for {email}: ")
    if not password:
        raise SystemExit("Password was empty.")
    save_password(email, password)
    print("Password saved in macOS Keychain.")
    return password


def _to_datetime(value: Any) -> datetime:
    """Convert Exchange dates to a stdlib UTC datetime.

    exchangelib's EWSDateTime is a datetime subclass, but its astimezone()
    only accepts EWSTimeZone — not datetime.timezone.utc.
    """
    if value is None:
        raise ValueError("missing datetime")
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return datetime(
                value.year,
                value.month,
                value.day,
                value.hour,
                value.minute,
                value.second,
                value.microsecond,
                tzinfo=timezone.utc,
            )
        return datetime.fromtimestamp(value.timestamp(), tz=timezone.utc)
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=timezone.utc)
    return datetime.fromtimestamp(value.timestamp(), tz=timezone.utc)


def _location(item: CalendarItem) -> str:
    loc = item.location
    if loc is None:
        return ""
    text = getattr(loc, "text", None)
    if text:
        return str(text)
    return str(loc)


def _notes(item: CalendarItem) -> str:
    text = getattr(item, "text_body", None) or item.body or ""
    return str(text)[:8000]


def connect(settings: EwsSettings, password: str | None = None) -> Account:
    BaseProtocol.TIMEOUT = EWS_TIMEOUT_SECONDS
    if not settings.verify_ssl:
        BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter
        warnings.filterwarnings("ignore", category=InsecureRequestWarning)
    secret = password or password_for(settings.email)
    credentials = Credentials(username=settings.username, password=secret)
    config = Configuration(
        server=settings.server,
        credentials=credentials,
        auth_type=_auth_type(settings.auth),
    )
    try:
        return Account(
            primary_smtp_address=settings.email,
            config=config,
            autodiscover=False,
            access_type=DELEGATE,
        )
    except UnauthorizedError as exc:
        raise SystemExit(
            "Exchange rejected the username/password.\n"
            "Try ews.username as your full email, or as DOMAIN\\account "
            "(example: DIGIKALA\\your.name).\n"
            "If NTLM fails, set ews.auth: basic\n"
            f"Detail: {exc}"
        ) from exc
    except ErrorNonExistentMailbox as exc:
        raise SystemExit(
            f"Mailbox {settings.email} was not found on {settings.server}. "
            "Check ews.email.\n"
            f"Detail: {exc}"
        ) from exc
    except TransportError as exc:
        raise SystemExit(
            f"Could not reach https://{settings.server}/EWS/Exchange.asmx\n"
            "Connect the company VPN and confirm you can open mail.digikala.com "
            "in a browser. If the certificate is corporate-signed, set "
            "ews.verify_ssl: false\n"
            f"Detail: {exc}"
        ) from exc
    except Exception as exc:
        raise SystemExit(
            f"Exchange login failed ({type(exc).__name__}): {exc}\n"
            "Connect the VPN and run: python -m syncer login"
        ) from exc


def list_calendars(account: Account) -> list[CalendarInfo]:
    found: list[CalendarInfo] = []
    try:
        folders = list(account.root.walk())
    except Exception:
        folders = [account.calendar]
    if account.calendar not in folders:
        folders.insert(0, account.calendar)
    for folder in folders:
        if not isinstance(folder, Calendar):
            continue
        title = str(folder.name or "Calendar")
        found.append(
            CalendarInfo(
                identifier=str(getattr(folder, "id", title)),
                title=title,
                account=str(account.primary_smtp_address),
                label=title,
            )
        )
    found.sort(key=lambda item: item.label.lower())
    return found


def _resolve_folder(account: Account, wanted: str) -> Calendar:
    if not wanted:
        return account.calendar
    wanted_l = wanted.lower()
    if wanted_l in {account.calendar.name.lower(), "calendar"}:
        return account.calendar
    for folder in account.root.walk():
        if isinstance(folder, Calendar) and folder.name.lower() == wanted_l:
            return folder
    names = ", ".join(info.label for info in list_calendars(account)) or "(none)"
    raise SystemExit(
        f"No Exchange calendar named {wanted!r}. Available: {names}\n"
        "Put one of those names in config.yaml as ews.calendar, or leave it empty."
    )


def load_events(
    settings: EwsSettings,
    start: datetime,
    end: datetime,
    account: Account | None = None,
    *,
    include_notes: bool = True,
) -> list[SourceEvent]:
    account = account or connect(settings)
    folder = _resolve_folder(account, settings.calendar)
    # only() avoids per-item lazy fetches of body/attachments that hang on slow EWS.
    fields = [
        "id",
        "uid",
        "subject",
        "start",
        "end",
        "is_all_day",
        "location",
        "legacy_free_busy_status",
    ]
    if include_notes:
        fields.append("text_body")
    events: list[SourceEvent] = []
    try:
        items = folder.view(start=start, end=end).only(*fields)
    except Exception as exc:
        raise SystemExit(
            f"Timed out or failed reading Exchange calendar "
            f"(timeout {EWS_TIMEOUT_SECONDS}s).\n"
            "Connect the VPN and confirm OWA works, then retry.\n"
            f"Detail: {exc}"
        ) from exc
    for item in items:
        if not isinstance(item, CalendarItem):
            continue
        try:
            start_dt = _to_datetime(item.start)
            end_dt = _to_datetime(item.end)
        except Exception as exc:
            print(f"  skip  could not read event times ({exc})")
            continue
        uid = str(getattr(item, "uid", None) or item.id)
        free_busy = str(item.legacy_free_busy_status or "")
        events.append(
            SourceEvent(
                origin_id=f"{uid}|{start_dt.isoformat()}",
                title=str(item.subject or "(No title)"),
                start=start_dt,
                end=end_dt,
                all_day=bool(item.is_all_day),
                location=_location(item),
                notes=_notes(item) if include_notes else "",
                busy=free_busy not in {"Free", "NoData"},
                tentative=free_busy == "Tentative",
            )
        )
    events.sort(key=lambda item: item.start)
    return events
