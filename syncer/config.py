from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from .paths import bundle_dir, user_data_dir

# Writable project / app-support root (config, credentials, tokens, events.enc, logs).
ROOT = user_data_dir()
CONFIG_PATH = ROOT / "config.yaml"
# Example ships inside the app bundle when frozen; falls back to project tree in dev.
EXAMPLE_PATH = bundle_dir() / "config.example.yaml"
if not EXAMPLE_PATH.exists():
    EXAMPLE_PATH = ROOT / "config.example.yaml"

# Keep in sync with syncer.schedule.SCHEDULE_INTERVALS (avoid circular import here).
SCHEDULE_EVERY_CHOICES = ("15m", "30m", "1h", "3h", "6h", "12h")


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
    schedule_every: str
    credentials_path: Path
    token_path: Path
    config_path: Path


def _ews_settings(data: dict) -> EwsSettings:
    raw = data.get("ews") or {}
    email = str(raw.get("email", "")).strip()
    server = str(raw.get("server", "mail.digikala.com")).strip()
    if not email:
        raise ConfigError("config.yaml: set ews.email to your work address")
    if not server:
        raise ConfigError("config.yaml: set ews.server (for example mail.digikala.com)")
    auth = str(raw.get("auth", "ntlm")).strip().lower()
    if auth not in {"ntlm", "basic"}:
        raise ConfigError("config.yaml: ews.auth must be 'ntlm' or 'basic'")
    # Keep empty in config/UI; Exchange connect falls back to email when blank.
    username = str(raw.get("username", "")).strip()
    return EwsSettings(
        server=server,
        email=email,
        username=username,
        auth=auth,
        calendar=str(raw.get("calendar", "")).strip(),
        verify_ssl=bool(raw.get("verify_ssl", False)),
    )


def _parse_settings(data: dict, config_path: Path) -> Settings:
    privacy = str(data.get("privacy", "full")).strip().lower()
    if privacy not in {"full", "busy"}:
        raise ConfigError("config.yaml: privacy must be 'full' or 'busy'")
    source = str(data.get("source", "ews")).strip().lower()
    if source not in {"ews", "apple"}:
        raise ConfigError("config.yaml: source must be 'ews' or 'apple'")
    if source == "apple":
        import sys

        if sys.platform != "darwin":
            raise ConfigError(
                "config.yaml: source: apple is only supported on macOS.\n"
                "On Linux or Windows, set source: ews."
            )
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
    schedule_every = str(data.get("schedule_every", "15m")).strip().lower() or "15m"
    if schedule_every not in SCHEDULE_EVERY_CHOICES:
        raise ConfigError(
            "config.yaml: schedule_every must be one of "
            + ", ".join(SCHEDULE_EVERY_CHOICES)
        )
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
        schedule_every=schedule_every,
        credentials_path=ROOT / "credentials.json",
        token_path=ROOT / "token.json",
        config_path=config_path,
    )


def load_settings(path: Path | None = None) -> Settings:
    config_path = path or CONFIG_PATH
    if not config_path.exists():
        raise ConfigError(
            f"Missing {config_path.name}. Copy config.example.yaml to config.yaml "
            f"or run: python -m syncer setup / open the app and Save config"
        )
    data = yaml.safe_load(config_path.read_text()) or {}
    return _parse_settings(data, config_path)


def default_config_dict() -> dict[str, Any]:
    return {
        "source": "ews",
        "days_back": 7,
        "days_forward": 60,
        "privacy": "full",
        "ews": {
            "server": "mail.digikala.com",
            "email": "",
            "username": "",
            "auth": "ntlm",
            "calendar": "",
            "verify_ssl": False,
        },
        "apple_calendar": "Exchange / Calendar",
        "google_calendar": "Work (Outlook)",
        "timezone": "",
        "schedule_every": "15m",
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
        "schedule_every": settings.schedule_every,
    }
    if settings.ews is not None:
        payload["ews"] = asdict(settings.ews)
    else:
        payload["ews"] = default_config_dict()["ews"]
    return payload


def save_settings_dict(data: dict[str, Any], path: Path | None = None) -> Path:
    """Validate and write config.yaml. Returns the path written."""
    config_path = path or CONFIG_PATH
    merged = default_config_dict()
    merged.update({k: v for k, v in data.items() if k != "ews"})
    if "ews" in data and isinstance(data["ews"], dict):
        merged["ews"] = {**merged["ews"], **data["ews"]}
    parsed = _parse_settings(merged, config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
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


def migrate_legacy_template_defaults(path: Path | None = None) -> list[str]:
    """Upgrade old shipped template defaults to the current Digikala-oriented ones.

    Only touches configs that still use the old `mail.company.com` template host,
    so real user customizations are left alone.
    """
    config_path = path or CONFIG_PATH
    notes: list[str] = []
    if not config_path.exists():
        return notes
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    ews = dict(data.get("ews") or {}) if isinstance(data.get("ews"), dict) else {}
    server = str(ews.get("server", "")).strip()
    if server != "mail.company.com":
        return notes

    data["privacy"] = "full"
    ews["server"] = "mail.digikala.com"
    ews["verify_ssl"] = False
    data["ews"] = ews
    save_settings_dict(data, config_path)
    notes.append(
        "Updated template defaults → privacy=full, server=mail.digikala.com, verify_ssl=false"
    )
    return notes
