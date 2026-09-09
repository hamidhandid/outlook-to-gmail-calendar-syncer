from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yaml"
EXAMPLE_PATH = ROOT / "config.example.yaml"


@dataclass
class EwsSettings:
    server: str
    email: str
    username: str
    auth: str
    calendar: str
    verify_ssl: bool


@dataclass
class Settings:
    source: str
    days_back: int
    days_forward: int
    privacy: str
    apple_calendar: str
    ews: EwsSettings | None
    google_calendar: str
    timezone: str
    credentials_path: Path
    token_path: Path
    config_path: Path


def _ews_settings(data: dict) -> EwsSettings:
    raw = data.get("ews") or {}
    email = str(raw.get("email", "")).strip()
    server = str(raw.get("server", "mail.digikala.com")).strip()
    if not email:
        raise SystemExit("config.yaml: set ews.email to your work address")
    if not server:
        raise SystemExit("config.yaml: set ews.server (for example mail.digikala.com)")
    auth = str(raw.get("auth", "ntlm")).strip().lower()
    if auth not in {"ntlm", "basic"}:
        raise SystemExit("config.yaml: ews.auth must be 'ntlm' or 'basic'")
    username = str(raw.get("username", "")).strip() or email
    return EwsSettings(
        server=server,
        email=email,
        username=username,
        auth=auth,
        calendar=str(raw.get("calendar", "")).strip(),
        verify_ssl=bool(raw.get("verify_ssl", True)),
    )


def load_settings(path: Path | None = None) -> Settings:
    config_path = path or CONFIG_PATH
    if not config_path.exists():
        raise SystemExit(
            f"Missing {config_path.name}. Copy config.example.yaml to config.yaml and edit it:\n"
            f"  cp {EXAMPLE_PATH} {CONFIG_PATH}"
        )
    data = yaml.safe_load(config_path.read_text()) or {}
    privacy = str(data.get("privacy", "full")).strip().lower()
    if privacy not in {"full", "busy"}:
        raise SystemExit("config.yaml: privacy must be 'full' or 'busy'")
    source = str(data.get("source", "ews")).strip().lower()
    if source not in {"ews", "apple"}:
        raise SystemExit("config.yaml: source must be 'ews' or 'apple'")
    apple_calendar = str(data.get("apple_calendar", "")).strip()
    ews = _ews_settings(data) if source == "ews" else None
    if source == "apple" and not apple_calendar:
        raise SystemExit(
            "config.yaml: set apple_calendar to a name from `python -m syncer list-calendars`"
        )
    return Settings(
        source=source,
        days_back=int(data.get("days_back", 7)),
        days_forward=int(data.get("days_forward", 60)),
        privacy=privacy,
        apple_calendar=apple_calendar,
        ews=ews,
        google_calendar=str(data.get("google_calendar", "Work (Outlook)")).strip()
        or "Work (Outlook)",
        timezone=str(data.get("timezone", "")).strip(),
        credentials_path=ROOT / "credentials.json",
        token_path=ROOT / "token.json",
        config_path=config_path,
    )
