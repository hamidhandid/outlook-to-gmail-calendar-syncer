from __future__ import annotations

import os
import sys
from pathlib import Path
from textwrap import dedent

from .config import ROOT

LABEL = "com.outlook-to-gmail.calendar-syncer"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def _python() -> Path:
    return Path(sys.executable).resolve()


def install_schedule(interval_seconds: int = 900) -> None:
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    plist = dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
          <key>Label</key>
          <string>{LABEL}</string>
          <key>WorkingDirectory</key>
          <string>{ROOT}</string>
          <key>ProgramArguments</key>
          <array>
            <string>{_python()}</string>
            <string>-m</string>
            <string>syncer</string>
            <string>sync</string>
          </array>
          <key>StartInterval</key>
          <integer>{interval_seconds}</integer>
          <key>RunAtLoad</key>
          <true/>
          <key>StandardOutPath</key>
          <string>{logs / "sync.out.log"}</string>
          <key>StandardErrorPath</key>
          <string>{logs / "sync.err.log"}</string>
        </dict>
        </plist>
        """
    )
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.write_text(plist)
    uid = os.getuid()
    os.system(f'launchctl bootout gui/{uid} "{PLIST_PATH}" >/dev/null 2>&1')
    status = os.system(f'launchctl bootstrap gui/{uid} "{PLIST_PATH}"')
    if status != 0:
        raise SystemExit(
            f"Wrote {PLIST_PATH} but launchctl bootstrap failed. "
            "Try: launchctl bootstrap gui/$(id -u) "
            f'"{PLIST_PATH}"'
        )
    print(
        f"Scheduled sync every {interval_seconds // 60} minutes.\n"
        f"Plist: {PLIST_PATH}\n"
        "Keep this Mac on, and connect the company VPN so Calendar.app can refresh Outlook."
    )


def uninstall_schedule() -> None:
    uid = os.getuid()
    os.system(f'launchctl bootout gui/{uid} "{PLIST_PATH}" >/dev/null 2>&1')
    if PLIST_PATH.exists():
        PLIST_PATH.unlink()
        print(f"Removed {PLIST_PATH}")
    else:
        print("No schedule was installed.")
