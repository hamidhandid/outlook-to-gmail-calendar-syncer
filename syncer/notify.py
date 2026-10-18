from __future__ import annotations

import subprocess
from datetime import datetime

from .platform_util import is_macos

APP_NAME = "Outlook to Google Calendar Syncer"


def notify_sync_failed(*, when: datetime | None = None, detail: str = "") -> None:
    """Show a local macOS notification when a scheduled sync fails."""
    if not is_macos():
        return
    stamp = (when or datetime.now()).strftime("%H:%M")
    body = f"Could not sync events from Outlook at {stamp}"
    if detail:
        short = detail.strip().replace("\n", " ")
        if len(short) > 120:
            short = short[:117] + "…"
        body = f"{body}: {short}"
    # Escape for AppleScript string.
    safe_body = body.replace("\\", "\\\\").replace('"', '\\"')
    script = (
        f'display notification "{safe_body}" with title "{APP_NAME}" '
        f'subtitle "Scheduled sync failed"'
    )
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=False,
            capture_output=True,
            timeout=10,
        )
    except Exception:
        pass
