from __future__ import annotations

import os
import sys
from pathlib import Path

APP_SUPPORT_NAME = "outlook-to-gmail-calendar-syncer"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False)) or hasattr(sys, "_MEIPASS")


def bundle_dir() -> Path:
    """Read-only resources shipped with the app (or the project root in dev)."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent.parent


def user_data_dir() -> Path:
    """Writable folder for config, credentials, tokens, encrypted store, logs."""
    if is_frozen():
        if sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support" / APP_SUPPORT_NAME
        elif sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", str(Path.home()))) / APP_SUPPORT_NAME
        else:
            base = Path.home() / ".local" / "share" / APP_SUPPORT_NAME
        base.mkdir(parents=True, exist_ok=True)
        (base / "logs").mkdir(exist_ok=True)
        return base
    return Path(__file__).resolve().parent.parent


def runtime_executable() -> Path:
    return Path(sys.executable).resolve()


def sync_argv() -> list[str]:
    """Argv to run a background sync with the current interpreter / frozen binary."""
    exe = str(runtime_executable())
    if is_frozen():
        return [exe, "sync"]
    return [exe, "-m", "syncer", "sync"]


def read_version() -> str:
    for candidate in (bundle_dir() / "VERSION", user_data_dir() / "VERSION"):
        try:
            text = candidate.read_text(encoding="utf-8").strip()
            if text:
                return text
        except OSError:
            continue
    return "0.0.0"
