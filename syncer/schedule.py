from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

from .config import ROOT
from .platform_util import is_linux, is_macos, is_windows, platform_name

# --- macOS launchd (behavior intentionally unchanged) ---
LABEL = "com.outlook-to-gmail.calendar-syncer"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"

# --- Windows Task Scheduler ---
WINDOWS_TASK_NAME = "OutlookToGmailCalendarSyncer"
WINDOWS_RUNNER = ROOT / "run-sync-scheduled.cmd"

# --- Linux systemd --user ---
LINUX_UNIT = "outlook-to-gmail-syncer"
LINUX_SERVICE = Path.home() / ".config" / "systemd" / "user" / f"{LINUX_UNIT}.service"
LINUX_TIMER = Path.home() / ".config" / "systemd" / "user" / f"{LINUX_UNIT}.timer"


def _python() -> Path:
    return Path(sys.executable).resolve()


def install_schedule(interval_seconds: int = 900) -> None:
    if is_macos():
        _install_macos_launchd(interval_seconds)
        return
    if is_windows():
        _install_windows_task(interval_seconds)
        return
    if is_linux():
        _install_linux_systemd(interval_seconds)
        return
    raise SystemExit(
        f"install-schedule is not supported on {platform_name()}. "
        "Run `python -m syncer sync` from cron or your OS scheduler."
    )


def uninstall_schedule() -> None:
    if is_macos():
        _uninstall_macos_launchd()
        return
    if is_windows():
        _uninstall_windows_task()
        return
    if is_linux():
        _uninstall_linux_systemd()
        return
    raise SystemExit(f"uninstall-schedule is not supported on {platform_name()}.")


def _install_macos_launchd(interval_seconds: int = 900) -> None:
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


def _uninstall_macos_launchd() -> None:
    uid = os.getuid()
    os.system(f'launchctl bootout gui/{uid} "{PLIST_PATH}" >/dev/null 2>&1')
    if PLIST_PATH.exists():
        PLIST_PATH.unlink()
        print(f"Removed {PLIST_PATH}")
    else:
        print("No schedule was installed.")


def _write_windows_runner() -> Path:
    """Small .cmd so Task Scheduler gets a reliable cwd without nested quote hell."""
    python = _python()
    body = (
        "@echo off\r\n"
        f'cd /d "{ROOT}"\r\n'
        f'"{python}" -m syncer sync\r\n'
    )
    WINDOWS_RUNNER.write_text(body, encoding="utf-8", newline="\r\n")
    return WINDOWS_RUNNER


def _install_windows_task(interval_seconds: int = 900) -> None:
    minutes = max(1, interval_seconds // 60)
    runner = _write_windows_runner()
    create = [
        "schtasks",
        "/Create",
        "/F",
        "/TN",
        WINDOWS_TASK_NAME,
        "/SC",
        "MINUTE",
        "/MO",
        str(minutes),
        "/TR",
        str(runner),
    ]
    try:
        subprocess.run(create, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise SystemExit(
            "schtasks not found. Run install-schedule from a Windows Command Prompt."
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise SystemExit(
            "Failed to create Windows scheduled task.\n"
            f"Command: {' '.join(create)}\n"
            f"Detail: {detail or exc}"
        ) from exc
    print(
        f"Scheduled sync every {minutes} minutes via Task Scheduler.\n"
        f"Task name: {WINDOWS_TASK_NAME}\n"
        f"Runner: {runner}\n"
        "Connect the company VPN when Exchange must be reached."
    )


def _uninstall_windows_task() -> None:
    delete = ["schtasks", "/Delete", "/F", "/TN", WINDOWS_TASK_NAME]
    try:
        result = subprocess.run(delete, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise SystemExit("schtasks not found.") from exc
    if WINDOWS_RUNNER.exists():
        WINDOWS_RUNNER.unlink()
        print(f"Removed {WINDOWS_RUNNER}")
    if result.returncode != 0:
        print(
            f"No Windows task named {WINDOWS_TASK_NAME} (or delete failed).\n"
            f"{(result.stderr or result.stdout or '').strip()}"
        )
        return
    print(f"Removed Windows scheduled task: {WINDOWS_TASK_NAME}")


def _systemd_quote(path: Path) -> str:
    """Quote a path for systemd unit files when it contains spaces."""
    text = str(path)
    if any(ch.isspace() for ch in text):
        return f'"{text}"'
    return text


def _install_linux_systemd(interval_seconds: int = 900) -> None:
    minutes = max(1, interval_seconds // 60)
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    python = _python()
    out_log = logs / "sync.out.log"
    err_log = logs / "sync.err.log"

    LINUX_SERVICE.parent.mkdir(parents=True, exist_ok=True)
    LINUX_SERVICE.write_text(
        dedent(
            f"""\
            [Unit]
            Description=Outlook to Gmail calendar syncer

            [Service]
            Type=oneshot
            WorkingDirectory={_systemd_quote(ROOT)}
            ExecStart={_systemd_quote(python)} -m syncer sync
            StandardOutput=append:{out_log}
            StandardError=append:{err_log}
            """
        ),
        encoding="utf-8",
    )
    LINUX_TIMER.write_text(
        dedent(
            f"""\
            [Unit]
            Description=Run Outlook to Gmail calendar syncer every {minutes} minutes

            [Timer]
            OnBootSec=2min
            OnUnitActiveSec={minutes}min
            Persistent=true

            [Install]
            WantedBy=timers.target
            """
        ),
        encoding="utf-8",
    )

    commands = [
        ["systemctl", "--user", "daemon-reload"],
        ["systemctl", "--user", "enable", "--now", f"{LINUX_UNIT}.timer"],
    ]
    for cmd in commands:
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise SystemExit(
                "systemctl not found. On Linux this feature needs systemd --user.\n"
                f"You can instead add a cron line:\n"
                f"  */{minutes} * * * * cd {ROOT} && {python} -m syncer sync\n"
            ) from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "").strip()
            raise SystemExit(
                "Failed to enable systemd user timer.\n"
                "If this is a headless session, try: loginctl enable-linger $USER\n"
                f"Detail: {detail or exc}\n"
                f"Manual cron alternative:\n"
                f"  */{minutes} * * * * cd {ROOT} && {python} -m syncer sync"
            ) from exc

    print(
        f"Scheduled sync every {minutes} minutes via systemd --user.\n"
        f"Timer: {LINUX_TIMER}\n"
        f"Service: {LINUX_SERVICE}\n"
        "Connect the company VPN when Exchange must be reached.\n"
        f"Status: systemctl --user status {LINUX_UNIT}.timer"
    )


def _uninstall_linux_systemd() -> None:
    try:
        subprocess.run(
            ["systemctl", "--user", "disable", "--now", f"{LINUX_UNIT}.timer"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        pass
    removed = False
    for path in (LINUX_TIMER, LINUX_SERVICE):
        if path.exists():
            path.unlink()
            removed = True
            print(f"Removed {path}")
    try:
        subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        pass
    if not removed:
        print("No Linux systemd user timer/service was installed.")
