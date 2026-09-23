from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yaml"
EXAMPLE_PATH = ROOT / "config.example.yaml"


class ConfigError(Exception):
    """Invalid or missing configuration (safe for GUI and CLI)."""


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
    server = str(raw.get("server", "mail.company.com")).strip()
    if not email:
        raise ConfigError("config.yaml: set ews.email to your work address")
    if not server:
        raise ConfigError("config.yaml: set ews.server (for example mail.company.com)")
    auth = str(raw.get("auth", "ntlm")).strip().lower()
    if auth not in {"ntlm", "basic"}:
        raise ConfigError("config.yaml: ews.auth must be 'ntlm' or 'basic'")
    username = str(raw.get("username", "")).strip() or email
    return EwsSettings(
        server=server,
        email=email,
        username=username,
        auth=auth,
        calendar=str(raw.get("calendar", "")).strip(),
        verify_ssl=bool(raw.get("verify_ssl", True)),
    )


def _parse_settings(data: dict, config_path: Path) -> Settings:
    privacy = str(data.get("privacy", "full")).strip().lower()
    if privacy not in {"full", "busy"}:
        raise ConfigError("config.yaml: privacy must be 'full' or 'busy'")
    source = str(data.get("source", "ews")).strip().lower()
    if source not in {"ews", "apple"}:
        raise ConfigError("config.yaml: source must be 'ews' or 'apple'")
    apple_calendar = str(data.get("apple_calendar", "")).strip()
    ews = _ews_settings(data) if source == "ews" else None
    if source == "apple" and not apple_calendar:
        raise ConfigError(
            "config.yaml: set apple_calendar to a name from `python -m syncer list-calendars`"
        )
    try:
        days_back = int(data.get("days_back", 7))
        days_forward = int(data.get("days_forward", 60))
    except (TypeError, ValueError) as exc:
        raise ConfigError("days_back and days_forward must be integers") from exc
    return Settings(
        source=source,
        days_back=days_back,
        days_forward=days_forward,
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


def load_settings(path: Path | None = None) -> Settings:
    config_path = path or CONFIG_PATH
    if not config_path.exists():
        raise ConfigError(
            f"Missing {config_path.name}. Copy config.example.yaml to config.yaml "
            f"or run: python -m syncer setup / python -m syncer gui"
        )
    data = yaml.safe_load(config_path.read_text()) or {}
    return _parse_settings(data, config_path)


def default_config_dict() -> dict[str, Any]:
    return {
        "source": "ews",
        "days_back": 7,
        "days_forward": 60,
        "privacy": "busy",
        "ews": {
            "server": "mail.company.com",
            "email": "",
            "username": "",
            "auth": "ntlm",
            "calendar": "",
            "verify_ssl": True,
        },
        "apple_calendar": "Exchange / Calendar",
        "google_calendar": "Work (Outlook)",
        "timezone": "",
    }


def settings_to_dict(settings: Settings) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "source": settings.source,
        "days_back": settings.days_back,
        "days_forward": settings.days_forward,
        "privacy": settings.privacy,
        "apple_calendar": settings.apple_calendar,
        "google_calendar": settings.google_calendar,
        "timezone": settings.timezone,
    }
    if settings.ews is not None:
        payload["ews"] = asdict(settings.ews)
    else:
        payload["ews"] = default_config_dict()["ews"]
    return payload


def save_settings_dict(data: dict[str, Any], path: Path | None = None) -> Path:
    """Validate and write config.yaml. Returns the path written."""
    config_path = path or CONFIG_PATH
    # Fill defaults for missing keys so partial GUI saves still validate.
    merged = default_config_dict()
    merged.update({k: v for k, v in data.items() if k != "ews"})
    if "ews" in data and isinstance(data["ews"], dict):
        merged["ews"] = {**merged["ews"], **data["ews"]}
    parsed = _parse_settings(merged, config_path)
    config_path.write_text(
        yaml.safe_dump(settings_to_dict(parsed), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return config_path


def load_settings_dict(path: Path | None = None) -> dict[str, Any]:
    config_path = path or CONFIG_PATH
    if not config_path.exists():
        return default_config_dict()
    data = yaml.safe_load(config_path.read_text()) or {}
    merged = default_config_dict()
    merged.update({k: v for k, v in data.items() if k != "ews"})
    if isinstance(data.get("ews"), dict):
        merged["ews"] = {**merged["ews"], **data["ews"]}
    return merged
