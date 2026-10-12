from __future__ import annotations

import base64
import getpass
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import ROOT
from .models import SourceEvent

STORE_VERSION = 1
DEFAULT_STORE_PATH = ROOT / "events.enc"
_KDF_ITERATIONS = 480_000
_ENV_PASSWORD = "SYNCER_STORE_PASSWORD"


@dataclass
class StoredBundle:
    events: list[SourceEvent]
    privacy: str
    window_start: datetime
    window_end: datetime
    created_at: datetime
    path: Path


def default_store_path() -> Path:
    return DEFAULT_STORE_PATH


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def _prompt_password(*, confirm: bool) -> str:
    env = os.environ.get(_ENV_PASSWORD, "").strip()
    if env:
        return env
    password = getpass.getpass("Password for the encrypted events file: ")
    if not password:
        raise SystemExit("Password was empty.")
    if confirm:
        again = getpass.getpass("Confirm password: ")
        if password != again:
            raise SystemExit("Passwords did not match.")
    return password


def _event_to_dict(event: SourceEvent) -> dict[str, Any]:
    return {
        "origin_id": event.origin_id,
        "title": event.title,
        "start": event.start.isoformat(),
        "end": event.end.isoformat(),
        "all_day": event.all_day,
        "location": event.location,
        "notes": event.notes,
        "busy": event.busy,
        "tentative": event.tentative,
    }


def _event_from_dict(raw: dict[str, Any]) -> SourceEvent:
    return SourceEvent(
        origin_id=str(raw["origin_id"]),
        title=str(raw.get("title", "")),
        start=datetime.fromisoformat(str(raw["start"])),
        end=datetime.fromisoformat(str(raw["end"])),
        all_day=bool(raw.get("all_day", False)),
        location=str(raw.get("location", "")),
        notes=str(raw.get("notes", "")),
        busy=bool(raw.get("busy", True)),
        tentative=bool(raw.get("tentative", False)),
    )


def save_encrypted_events(
    events: list[SourceEvent],
    *,
    path: Path,
    privacy: str,
    window_start: datetime,
    window_end: datetime,
    password: str | None = None,
) -> Path:
    secret = password if password is not None else _prompt_password(confirm=True)
    payload = {
        "version": STORE_VERSION,
        "created_at": datetime.now().astimezone().isoformat(),
        "privacy": privacy,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "events": [_event_to_dict(event) for event in events],
    }
    plaintext = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    salt = os.urandom(16)
    token = Fernet(_derive_key(secret, salt)).encrypt(plaintext)
    envelope = {
        "format": "syncer-events-enc",
        "version": STORE_VERSION,
        "kdf": "pbkdf2-sha256",
        "iterations": _KDF_ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "ciphertext": base64.b64encode(token).decode("ascii"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def load_encrypted_events(
    path: Path,
    *,
    password: str | None = None,
) -> StoredBundle:
    if not path.exists():
        raise SystemExit(
            f"Encrypted events file not found: {path}\n"
            "Create one first with: python -m syncer store"
        )
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Encrypted events file is not valid JSON: {path}") from exc

    if envelope.get("format") != "syncer-events-enc":
        raise SystemExit(f"Unrecognized encrypted events file: {path}")

    secret = password if password is not None else _prompt_password(confirm=False)
    try:
        salt = base64.b64decode(envelope["salt"])
        ciphertext = base64.b64decode(envelope["ciphertext"])
        plaintext = Fernet(_derive_key(secret, salt)).decrypt(ciphertext)
        payload = json.loads(plaintext.decode("utf-8"))
    except (KeyError, ValueError, InvalidToken, json.JSONDecodeError) as exc:
        raise SystemExit(
            "Could not decrypt the events file. Check the password, "
            "or recreate it with: python -m syncer store"
        ) from exc

    events = [_event_from_dict(item) for item in payload.get("events", [])]
    return StoredBundle(
        events=events,
        privacy=str(payload.get("privacy", "busy")),
        window_start=datetime.fromisoformat(str(payload["window_start"])),
        window_end=datetime.fromisoformat(str(payload["window_end"])),
        created_at=datetime.fromisoformat(str(payload["created_at"])),
        path=path,
    )
