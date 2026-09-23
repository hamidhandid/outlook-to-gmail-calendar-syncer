from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk
import yaml

from .api import (
    check_tokens_status,
    format_event_row,
    get_events,
    login_exchange,
    reauth_google,
    run_sync,
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
        self.title("Outlook → Google Calendar")
        self.geometry("920x740")
        self.minsize(780, 620)

        self._events: list[SourceEvent] = []
        self._busy = False
        self._cancel = threading.Event()

        self._build()
        self._load_config_into_form()
        self._report_bootstrap()
        self._set_status("Ready. Save config, then Get events (VPN on).", "info")

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkLabel(
            self,
            text="Outlook → Google Calendar Sync",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        header.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

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

        save_btn = ctk.CTkButton(config, text="Save config", width=110, command=self._save_config)
        save_btn.grid(row=3, column=3, padx=8, pady=6, sticky="e")

        setup_btn = ctk.CTkButton(
            config, text="Setup Google", width=120, command=self._on_setup_google
        )
        setup_btn.grid(row=3, column=4, padx=8, pady=6, sticky="e")

        import_btn = ctk.CTkButton(
            config, text="Import credentials…", width=140, command=self._on_import_credentials
        )
        import_btn.grid(row=3, column=5, padx=8, pady=6, sticky="e")

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
        actions.grid(row=4, column=0, padx=16, pady=(0, 8), sticky="ew")

        self.get_btn = ctk.CTkButton(actions, text="Get", width=100, command=self._on_get)
        self.get_btn.pack(side="left", padx=6, pady=8)

        self.sync_btn = ctk.CTkButton(
            actions, text="Sync", width=100, command=self._on_sync, state="disabled"
        )
        self.sync_btn.pack(side="left", padx=6, pady=8)

        self.stop_btn = ctk.CTkButton(
            actions,
            text="Stop",
            width=100,
            fg_color=ERROR_COLOR,
            hover_color="#a32f2f",
            command=self._on_stop,
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=6, pady=8)

        self.tokens_btn = ctk.CTkButton(
            actions, text="Check tokens", width=120, command=self._on_tokens
        )
        self.tokens_btn.pack(side="left", padx=6, pady=8)

        self.login_btn = ctk.CTkButton(
            actions, text="Login Exchange", width=130, command=self._on_login
        )
        self.login_btn.pack(side="left", padx=6, pady=8)

        self.reauth_btn = ctk.CTkButton(
            actions, text="Reauth Google", width=120, command=self._on_reauth
        )
        self.reauth_btn.pack(side="left", padx=6, pady=8)

        self.status = ctk.CTkLabel(self, text="", anchor="w")
        self.status.grid(row=5, column=0, padx=16, pady=(0, 16), sticky="ew")

    def _report_bootstrap(self) -> None:
        for note in ensure_user_files():
            level = "info"
            if note.startswith("Created") or note.startswith("Missing"):
                level = "info"
            self._append_log(level, note)
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
        self.get_btn.configure(state=state)
        self.tokens_btn.configure(state=state)
        self.login_btn.configure(state=state)
        self.reauth_btn.configure(state=state)
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
        if not self._events:
            self._set_status("Get events first.", "error")
            return
        if not CREDENTIALS_PATH.exists():
            self._set_status("Missing credentials.json — Setup Google first.", "error")
            return
        if not self._save_config():
            return

        def work() -> None:
            settings = load_settings()
            result = run_sync(
                settings,
                events=list(self._events),
                dry_run=False,
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

    def _on_tokens(self) -> None:
        if not self._save_config():
            return

        def work() -> None:
            result = check_tokens_status(log=self._gui_log)

            def done() -> None:
                self._set_status(result.message, "success" if result.ok else "error")

            self.after(0, done)

        self._run_async(work)

    def _on_login(self) -> None:
        if not self._save_config():
            return
        dialog = ctk.CTkInputDialog(
            text=f"Exchange password for {self.email.get().strip()}:",
            title="Login Exchange",
        )
        password = dialog.get_input()
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
            "If the company VPN blocks Google, disconnect it briefly.",
        ):
            return

        def work() -> None:
            ok, msg = reauth_google(log=self._gui_log)

            def done() -> None:
                self._set_status(msg, "success" if ok else "error")

            self.after(0, done)

        self._run_async(work)

    def _on_setup_google(self) -> None:
        if not messagebox.askyesno(
            "Setup Google",
            "Open the guided Google Cloud OAuth setup in the terminal flow?\n"
            "(Browser pages will open. Prefer disconnecting VPN if Google is blocked.)",
        ):
            return

        def work() -> None:
            try:
                from .wizard import walk_google_oauth

                walk_google_oauth()
                msg = "Google setup finished (or skipped). Check credentials.json."
                self._gui_log("success", msg)
            except Exception as exc:
                msg = f"Google setup failed: {exc}"
                self._gui_log("error", msg)

            def done() -> None:
                if CREDENTIALS_PATH.exists():
                    self._set_status("credentials.json is present.", "success")
                else:
                    self._set_status(msg, "error")

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
