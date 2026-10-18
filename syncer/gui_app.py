from __future__ import annotations

import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
from typing import Any

import customtkinter as ctk
import yaml

from . import __version__
from .api import (
    check_tokens_status,
    format_event_row,
    get_events,
    login_exchange,
    reauth_google,
    run_sync,
    run_sync_from_encrypted,
    store_events_encrypted,
)
from .bootstrap import CREDENTIALS_PATH, ensure_user_files
from .config import (
    CONFIG_PATH,
    ROOT,
    ConfigError,
    load_settings,
    load_settings_dict,
    save_settings_dict,
)
from .models import SourceEvent

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

SUCCESS_COLOR = "#1a7f37"
ERROR_COLOR = "#c23b3b"
INFO_COLOR_LIGHT = "#333333"
INFO_COLOR_DARK = "#dddddd"


class SyncerApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Outlook → Google Calendar  v{__version__}")
        self.geometry("980x820")
        self.minsize(820, 680)

        self._events: list[SourceEvent] = []
        self._busy = False
        self._cancel = threading.Event()

        self._build()
        self._load_config_into_form()
        self._report_bootstrap()
        self._set_status("Ready. Save config, then Get events (company VPN on).", "info")

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkLabel(
            self,
            text="Outlook → Google Calendar Sync",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        header.grid(row=0, column=0, padx=16, pady=(16, 4), sticky="w")

        ctk.CTkLabel(
            self,
            text=f"Data folder: {ROOT}",
            font=ctk.CTkFont(size=11),
            text_color="gray50",
        ).grid(row=0, column=0, padx=16, pady=(40, 0), sticky="w")

        config = ctk.CTkFrame(self)
        config.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        config.grid_columnconfigure((1, 3, 5), weight=1)

        ctk.CTkLabel(config, text="days_back").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        self.days_back = ctk.CTkEntry(config, width=80)
        self.days_back.grid(row=0, column=1, padx=8, pady=6, sticky="w")

        ctk.CTkLabel(config, text="days_forward").grid(row=0, column=2, padx=8, pady=6, sticky="w")
        self.days_forward = ctk.CTkEntry(config, width=80)
        self.days_forward.grid(row=0, column=3, padx=8, pady=6, sticky="w")

        ctk.CTkLabel(config, text="privacy").grid(row=0, column=4, padx=8, pady=6, sticky="w")
        self.privacy = ctk.CTkOptionMenu(config, values=["busy", "full"], width=100)
        self.privacy.grid(row=0, column=5, padx=8, pady=6, sticky="w")

        ctk.CTkLabel(config, text="email").grid(row=1, column=0, padx=8, pady=6, sticky="w")
        self.email = ctk.CTkEntry(config)
        self.email.grid(row=1, column=1, columnspan=2, padx=8, pady=6, sticky="ew")

        ctk.CTkLabel(config, text="server").grid(row=1, column=3, padx=8, pady=6, sticky="w")
        self.server = ctk.CTkEntry(config)
        self.server.grid(row=1, column=4, columnspan=2, padx=8, pady=6, sticky="ew")

        ctk.CTkLabel(config, text="username").grid(row=2, column=0, padx=8, pady=6, sticky="w")
        self.username = ctk.CTkEntry(config, placeholder_text="empty = email")
        self.username.grid(row=2, column=1, columnspan=2, padx=8, pady=6, sticky="ew")

        ctk.CTkLabel(config, text="auth").grid(row=2, column=3, padx=8, pady=6, sticky="w")
        self.auth = ctk.CTkOptionMenu(config, values=["ntlm", "basic"], width=100)
        self.auth.grid(row=2, column=4, padx=8, pady=6, sticky="w")

        self.verify_ssl = ctk.CTkCheckBox(config, text="verify SSL")
        self.verify_ssl.grid(row=2, column=5, padx=8, pady=6, sticky="w")

        ctk.CTkLabel(config, text="Google calendar").grid(
            row=3, column=0, padx=8, pady=6, sticky="w"
        )
        self.google_calendar = ctk.CTkEntry(config)
        self.google_calendar.grid(row=3, column=1, columnspan=2, padx=8, pady=6, sticky="ew")

        ctk.CTkButton(config, text="Save config", width=110, command=self._save_config).grid(
            row=3, column=3, padx=8, pady=6, sticky="e"
        )
        ctk.CTkButton(
            config, text="Setup Google", width=120, command=self._on_setup_google
        ).grid(row=3, column=4, padx=8, pady=6, sticky="e")
        ctk.CTkButton(
            config, text="Import credentials…", width=140, command=self._on_import_credentials
        ).grid(row=3, column=5, padx=8, pady=6, sticky="e")

        events_frame = ctk.CTkFrame(self)
        events_frame.grid(row=2, column=0, padx=16, pady=8, sticky="nsew")
        events_frame.grid_columnconfigure(0, weight=1)
        events_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(events_frame, text="Outlook events", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=8, pady=(8, 4), sticky="w"
        )
        self.events_box = ctk.CTkTextbox(events_frame, font=ctk.CTkFont(family="Menlo", size=12))
        self.events_box.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")
        self.events_box.insert("1.0", "Click Get to load events from Outlook/Exchange.\n")
        self.events_box.configure(state="disabled")

        logs_frame = ctk.CTkFrame(self)
        logs_frame.grid(row=3, column=0, padx=16, pady=8, sticky="nsew")
        logs_frame.grid_columnconfigure(0, weight=1)
        logs_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(logs_frame, text="Logs", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=8, pady=(8, 4), sticky="w"
        )
        self.logs = ctk.CTkTextbox(logs_frame, font=ctk.CTkFont(family="Menlo", size=12))
        self.logs.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")
        self._init_log_tags()

        actions = ctk.CTkFrame(self)
        actions.grid(row=4, column=0, padx=16, pady=(0, 4), sticky="ew")

        self.get_btn = ctk.CTkButton(actions, text="Get", width=90, command=self._on_get)
        self.get_btn.pack(side="left", padx=4, pady=6)

        self.sync_btn = ctk.CTkButton(
            actions, text="Sync", width=90, command=self._on_sync, state="disabled"
        )
        self.sync_btn.pack(side="left", padx=4, pady=6)

        self.dry_btn = ctk.CTkButton(
            actions, text="Sync dry-run", width=110, command=self._on_sync_dry
        )
        self.dry_btn.pack(side="left", padx=4, pady=6)

        self.stop_btn = ctk.CTkButton(
            actions,
            text="Stop",
            width=80,
            fg_color=ERROR_COLOR,
            hover_color="#a32f2f",
            command=self._on_stop,
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=4, pady=6)

        self.tokens_btn = ctk.CTkButton(
            actions, text="Check tokens", width=110, command=self._on_tokens
        )
        self.tokens_btn.pack(side="left", padx=4, pady=6)

        self.login_btn = ctk.CTkButton(
            actions, text="Login Exchange", width=120, command=self._on_login
        )
        self.login_btn.pack(side="left", padx=4, pady=6)

        self.reauth_btn = ctk.CTkButton(
            actions, text="Reauth Google", width=110, command=self._on_reauth
        )
        self.reauth_btn.pack(side="left", padx=4, pady=6)

        more = ctk.CTkFrame(self)
        more.grid(row=5, column=0, padx=16, pady=(0, 4), sticky="ew")

        self.store_btn = ctk.CTkButton(
            more, text="Store encrypted", width=130, command=self._on_store
        )
        self.store_btn.pack(side="left", padx=4, pady=6)

        self.sync_stored_btn = ctk.CTkButton(
            more, text="Sync from file", width=120, command=self._on_sync_stored
        )
        self.sync_stored_btn.pack(side="left", padx=4, pady=6)

        self.list_cal_btn = ctk.CTkButton(
            more, text="List calendars", width=120, command=self._on_list_calendars
        )
        self.list_cal_btn.pack(side="left", padx=4, pady=6)

        self.check_btn = ctk.CTkButton(more, text="Check", width=80, command=self._on_check)
        self.check_btn.pack(side="left", padx=4, pady=6)

        self.sched_btn = ctk.CTkButton(
            more, text="Install schedule", width=130, command=self._on_install_schedule
        )
        self.sched_btn.pack(side="left", padx=4, pady=6)

        self.unsched_btn = ctk.CTkButton(
            more, text="Uninstall schedule", width=140, command=self._on_uninstall_schedule
        )
        self.unsched_btn.pack(side="left", padx=4, pady=6)

        self.data_btn = ctk.CTkButton(
            more, text="Open data folder", width=130, command=self._on_open_data
        )
        self.data_btn.pack(side="left", padx=4, pady=6)

        self._action_buttons = [
            self.get_btn,
            self.dry_btn,
            self.tokens_btn,
            self.login_btn,
            self.reauth_btn,
            self.store_btn,
            self.sync_stored_btn,
            self.list_cal_btn,
            self.check_btn,
            self.sched_btn,
            self.unsched_btn,
            self.data_btn,
        ]

        self.status = ctk.CTkLabel(self, text="", anchor="w")
        self.status.grid(row=6, column=0, padx=16, pady=(0, 16), sticky="ew")

    def _report_bootstrap(self) -> None:
        for note in ensure_user_files():
            self._append_log("info", note)
        if not CREDENTIALS_PATH.exists():
            self._append_log(
                "error",
                "No credentials.json yet. Click Setup Google or Import credentials…",
            )

    def _init_log_tags(self) -> None:
        text: tk.Text = self.logs._textbox  # noqa: SLF001
        text.tag_configure("success", foreground=SUCCESS_COLOR)
        text.tag_configure("error", foreground=ERROR_COLOR)
        appearance = ctk.get_appearance_mode()
        info = INFO_COLOR_DARK if appearance == "Dark" else INFO_COLOR_LIGHT
        text.tag_configure("info", foreground=info)

    def _load_config_into_form(self) -> None:
        data = load_settings_dict()
        ews = data.get("ews") or {}
        self.days_back.delete(0, "end")
        self.days_back.insert(0, str(data.get("days_back", 7)))
        self.days_forward.delete(0, "end")
        self.days_forward.insert(0, str(data.get("days_forward", 60)))
        self.privacy.set(str(data.get("privacy", "busy")))
        self.email.delete(0, "end")
        self.email.insert(0, str(ews.get("email", "")))
        self.server.delete(0, "end")
        self.server.insert(0, str(ews.get("server", "mail.company.com")))
        self.username.delete(0, "end")
        self.username.insert(0, str(ews.get("username", "")))
        self.auth.set(str(ews.get("auth", "ntlm")))
        if ews.get("verify_ssl", True):
            self.verify_ssl.select()
        else:
            self.verify_ssl.deselect()
        self.google_calendar.delete(0, "end")
        self.google_calendar.insert(0, str(data.get("google_calendar", "Work (Outlook)")))

    def _form_to_dict(self) -> dict[str, Any]:
        return {
            "source": "ews",
            "days_back": int(self.days_back.get().strip() or "7"),
            "days_forward": int(self.days_forward.get().strip() or "60"),
            "privacy": self.privacy.get(),
            "google_calendar": self.google_calendar.get().strip() or "Work (Outlook)",
            "timezone": "",
            "apple_calendar": "Exchange / Calendar",
            "ews": {
                "server": self.server.get().strip(),
                "email": self.email.get().strip(),
                "username": self.username.get().strip(),
                "auth": self.auth.get(),
                "calendar": "",
                "verify_ssl": bool(self.verify_ssl.get()),
            },
        }

    def _save_config(self) -> bool:
        try:
            data = self._form_to_dict()
            path = save_settings_dict(data)
        except (ConfigError, ValueError) as exc:
            self._append_log("error", str(exc))
            self._set_status(f"Config not saved: {exc}", "error")
            return False
        self._append_log("success", f"Saved {path}")
        self._set_status("Config saved.", "success")
        self._events = []
        self.sync_btn.configure(state="disabled")
        return True

    def _set_status(self, message: str, level: str = "info") -> None:
        colors = {
            "success": SUCCESS_COLOR,
            "error": ERROR_COLOR,
            "info": ("gray70" if ctk.get_appearance_mode() == "Dark" else "gray30"),
        }
        self.status.configure(text=message, text_color=colors.get(level, colors["info"]))

    def _append_log(self, level: str, message: str) -> None:
        self._init_log_tags()
        self.logs.configure(state="normal")
        tag = level if level in {"success", "error", "info"} else "info"
        self.logs.insert("end", message.rstrip() + "\n", tag)
        self.logs.see("end")

    def _set_events_text(self, lines: list[str]) -> None:
        self.events_box.configure(state="normal")
        self.events_box.delete("1.0", "end")
        self.events_box.insert("1.0", "\n".join(lines) + ("\n" if lines else ""))
        self.events_box.configure(state="disabled")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        for btn in self._action_buttons:
            btn.configure(state=state)
        self.stop_btn.configure(state="normal" if busy else "disabled")
        if busy:
            self.sync_btn.configure(state="disabled")
        elif self._events:
            self.sync_btn.configure(state="normal")

    def _run_async(self, work) -> None:
        if self._busy:
            return
        self._cancel.clear()

        def runner() -> None:
            self.after(0, lambda: self._set_busy(True))
            try:
                work()
            finally:
                self.after(0, lambda: self._set_busy(False))

        threading.Thread(target=runner, daemon=True).start()

    def _gui_log(self, level: str, message: str) -> None:
        self.after(0, lambda: self._append_log(level, message))

    def _ask_password(self, prompt: str) -> str | None:
        # simpledialog works for hidden-ish prompts; CTkInputDialog shows text.
        return simpledialog.askstring("Password", prompt, show="*", parent=self)

    def _on_stop(self) -> None:
        self._cancel.set()
        self._append_log("info", "Stop requested — waiting for the current step to finish…")
        self._set_status("Stopping…", "info")

    def _on_get(self) -> None:
        if not CREDENTIALS_PATH.exists():
            self._append_log("error", "Add credentials.json first (Setup Google / Import).")
        if not self._save_config():
            return

        def work() -> None:
            settings = load_settings()
            result = get_events(settings, log=self._gui_log, cancel=self._cancel)

            def done() -> None:
                if not result.ok:
                    self._events = []
                    self.sync_btn.configure(state="disabled")
                    self._set_events_text([result.message or "Get failed."])
                    level = "info" if "Cancelled" in (result.message or "") else "error"
                    self._set_status(result.message or "Get failed.", level)
                    return
                self._events = list(result.events)
                if not self._events:
                    self._set_events_text(["No events in this date window."])
                    self.sync_btn.configure(state="disabled")
                else:
                    rows = [
                        format_event_row(ev, settings.privacy, settings.timezone)
                        for ev in self._events
                    ]
                    self._set_events_text(rows)
                    self.sync_btn.configure(state="normal")
                self._set_status(result.message, "success")

            self.after(0, done)

        self._run_async(work)

    def _on_sync(self) -> None:
        self._sync_live(dry_run=False)

    def _on_sync_dry(self) -> None:
        self._sync_live(dry_run=True)

    def _sync_live(self, *, dry_run: bool) -> None:
        if not CREDENTIALS_PATH.exists():
            self._set_status("Missing credentials.json — Setup Google first.", "error")
            return
        if not dry_run and not self._events:
            self._set_status("Get events first (or use Sync dry-run to fetch+preview).", "error")
            return
        if not self._save_config():
            return

        def work() -> None:
            settings = load_settings()
            result = run_sync(
                settings,
                events=list(self._events) if self._events else None,
                dry_run=dry_run,
                log=self._gui_log,
                cancel=self._cancel,
            )

            def done() -> None:
                if result.ok:
                    self._set_status(result.message, "success")
                else:
                    level = "info" if "Cancelled" in (result.message or "") else "error"
                    self._set_status(result.message or "Sync failed.", level)

            self.after(0, done)

        self._run_async(work)

    def _on_store(self) -> None:
        if not self._save_config():
            return
        password = self._ask_password("Choose a password for the encrypted events file:")
        if not password:
            self._set_status("Store cancelled.", "info")
            return
        confirm = self._ask_password("Confirm password:")
        if password != confirm:
            self._set_status("Passwords did not match.", "error")
            return

        def work() -> None:
            result = store_events_encrypted(
                password=password, log=self._gui_log, cancel=self._cancel
            )

            def done() -> None:
                self._set_status(result.message.split("\n")[0], "success" if result.ok else "error")

            self.after(0, done)

        self._run_async(work)

    def _on_sync_stored(self) -> None:
        if not CREDENTIALS_PATH.exists():
            self._set_status("Missing credentials.json — Setup Google first.", "error")
            return
        if not self._save_config():
            return
        password = self._ask_password("Password for the encrypted events file:")
        if not password:
            self._set_status("Sync from file cancelled.", "info")
            return

        def work() -> None:
            result = run_sync_from_encrypted(
                password=password,
                dry_run=False,
                log=self._gui_log,
                cancel=self._cancel,
            )

            def done() -> None:
                self._set_status(
                    result.message or ("OK" if result.ok else "Failed"),
                    "success" if result.ok else "error",
                )

            self.after(0, done)

        self._run_async(work)

    def _on_tokens(self) -> None:
        if not self._save_config():
            return

        def work() -> None:
            result = check_tokens_status(log=self._gui_log)

            def done() -> None:
                self._set_status(result.message, "success" if result.ok else "error")

            self.after(0, done)

        self._run_async(work)

    def _on_check(self) -> None:
        self._on_tokens()

    def _on_login(self) -> None:
        if not self._save_config():
            return
        password = self._ask_password(f"Exchange password for {self.email.get().strip()}:")
        if not password:
            self._set_status("Login cancelled.", "info")
            return

        def work() -> None:
            ok, msg = login_exchange(password=password, log=self._gui_log)

            def done() -> None:
                self._set_status(msg, "success" if ok else "error")

            self.after(0, done)

        self._run_async(work)

    def _on_reauth(self) -> None:
        if not CREDENTIALS_PATH.exists():
            self._set_status("Missing credentials.json — Setup Google first.", "error")
            return
        if not messagebox.askyesno(
            "Reauth Google",
            "This opens a browser to sign in to Google again.\n"
            "If the company VPN blocks Google, use a personal VPN briefly.",
        ):
            return

        def work() -> None:
            ok, msg = reauth_google(log=self._gui_log)

            def done() -> None:
                self._set_status(msg, "success" if ok else "error")

            self.after(0, done)

        self._run_async(work)

    def _on_list_calendars(self) -> None:
        if not self._save_config():
            return

        def work() -> None:
            lines: list[str] = []
            try:
                settings = load_settings()
                if settings.source == "ews" and settings.ews is not None:
                    from . import ews

                    account = ews.connect(settings.ews)
                    lines.append(
                        f"Exchange calendars on {settings.ews.server} "
                        f"as {settings.ews.email}:"
                    )
                    found = ews.list_calendars(account)
                    if not found:
                        lines.append("  (none — default mailbox calendar will be used)")
                    else:
                        lines.extend(f"  {info.label}" for info in found)
                else:
                    from . import apple

                    lines.append("Apple calendars:")
                    lines.extend(f"  {info.label}" for info in apple.list_calendars())
                self._gui_log("success", "Listed calendars.")
            except SystemExit as exc:
                msg = str(exc.code) if isinstance(exc.code, str) else str(exc)
                lines = [msg]
                self._gui_log("error", msg)
            except Exception as exc:
                lines = [str(exc)]
                self._gui_log("error", str(exc))

            def done() -> None:
                self._set_events_text(lines)
                self._set_status("Calendar list updated.", "info")

            self.after(0, done)

        self._run_async(work)

    def _on_install_schedule(self) -> None:
        if not messagebox.askyesno(
            "Install schedule",
            "Run sync automatically every 15 minutes while this Mac is on?",
        ):
            return

        def work() -> None:
            try:
                from .schedule import install_schedule

                install_schedule()
                msg = "Schedule installed (every 15 minutes)."
                self._gui_log("success", msg)
            except SystemExit as exc:
                msg = str(exc.code) if isinstance(exc.code, str) else str(exc)
                self._gui_log("error", msg)
            except Exception as exc:
                msg = str(exc)
                self._gui_log("error", msg)

            def done() -> None:
                self._set_status(msg, "success" if "installed" in msg.lower() else "error")

            self.after(0, done)

        self._run_async(work)

    def _on_uninstall_schedule(self) -> None:
        def work() -> None:
            try:
                from .schedule import uninstall_schedule

                uninstall_schedule()
                msg = "Schedule removed."
                self._gui_log("success", msg)
            except SystemExit as exc:
                msg = str(exc.code) if isinstance(exc.code, str) else str(exc)
                self._gui_log("error", msg)
            except Exception as exc:
                msg = str(exc)
                self._gui_log("error", msg)

            def done() -> None:
                self._set_status(msg, "info")

            self.after(0, done)

        self._run_async(work)

    def _on_open_data(self) -> None:
        ROOT.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(ROOT)], check=False)
            elif sys.platform == "win32":
                subprocess.run(["explorer", str(ROOT)], check=False)
            else:
                subprocess.run(["xdg-open", str(ROOT)], check=False)
            self._set_status(f"Opened {ROOT}", "success")
        except Exception as exc:
            self._set_status(f"Could not open folder: {exc}", "error")

    def _on_setup_google(self) -> None:
        from .wizard import walk_google_oauth_gui

        def ask_continue(title: str, message: str) -> bool:
            return bool(messagebox.askokcancel(title, message, parent=self))

        def work() -> None:
            try:
                ok = walk_google_oauth_gui(ask_continue=ask_continue, log=self._gui_log)
                msg = (
                    "Google setup finished."
                    if ok and CREDENTIALS_PATH.exists()
                    else "Google setup incomplete — use Import credentials… if needed."
                )
            except Exception as exc:
                ok = False
                msg = f"Google setup failed: {exc}"
                self._gui_log("error", msg)

            def done() -> None:
                self._set_status(
                    msg,
                    "success" if CREDENTIALS_PATH.exists() else "error",
                )

            self.after(0, done)

        self._run_async(work)

    def _on_import_credentials(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Google OAuth Desktop client JSON",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        src = Path(path)
        try:
            CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
            CREDENTIALS_PATH.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        except OSError as exc:
            self._append_log("error", f"Could not copy credentials: {exc}")
            self._set_status("Import failed.", "error")
            return
        self._append_log("success", f"Imported credentials.json from {src}")
        self._set_status("credentials.json saved.", "success")


def run_gui() -> None:
    ensure_user_files()
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(
            yaml.safe_dump(load_settings_dict(), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    app = SyncerApp()
    app.mainloop()
