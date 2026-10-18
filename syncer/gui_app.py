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
    check_google_auth,
    check_outlook_auth,
    format_event_row,
    get_events,
    login_exchange,
    reauth_google,
    remove_google_credentials,
    reset_credentials_and_calendar,
    run_sync,
    run_sync_from_encrypted,
    store_events_encrypted,
)
from .bootstrap import CREDENTIALS_PATH, TOKEN_PATH, ensure_user_files
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
# First button in each action row (distinct from the default blue).
ROW_LEAD_COLOR = "#0f766e"
ROW_LEAD_HOVER = "#0d9488"


class SyncerApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Outlook to Google Calendar Syncer  v{__version__}")
        self.geometry("1100x980")
        self.minsize(920, 820)

        self._events: list[SourceEvent] = []
        self._busy = False
        self._cancel = threading.Event()

        self._build()
        # Bootstrap/migrate before loading the form so Digikala defaults appear.
        self._report_bootstrap()
        self._load_config_into_form()
        self._refresh_auth_buttons()
        self._refresh_reset_button()
        self._set_status(
            "Ready. Save config, then Show events from outlook (company VPN on).",
            "info",
        )

    def _lead_button(self, parent: ctk.CTkFrame, text: str, command, width: int = 160) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text=text,
            width=width,
            command=command,
            fg_color=ROW_LEAD_COLOR,
            hover_color=ROW_LEAD_HOVER,
        )

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=16, pady=(16, 4), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Outlook to Google Calendar Syncer",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        data_row = ctk.CTkFrame(header, fg_color="transparent")
        data_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        data_row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            data_row,
            text=f"Data folder: {ROOT}",
            font=ctk.CTkFont(size=11),
            text_color="gray50",
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        self.data_btn = ctk.CTkButton(
            data_row, text="Open data folder", width=140, command=self._on_open_data
        )
        self.data_btn.grid(row=0, column=1, padx=(8, 0), sticky="e")

        top = ctk.CTkFrame(self)
        top.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        top.grid_columnconfigure(0, weight=3)
        top.grid_columnconfigure(2, weight=2)

        # —— Section 1 (left): config + inline Outlook/Google setup ——
        left = ctk.CTkFrame(top, fg_color="transparent")
        left.grid(row=0, column=0, padx=(8, 4), pady=8, sticky="nsew")
        left.grid_columnconfigure(1, weight=1)

        # Row 1 — days_back + days_forward
        row_days = ctk.CTkFrame(left, fg_color="transparent")
        row_days.grid(row=0, column=0, columnspan=2, padx=4, pady=3, sticky="ew")
        ctk.CTkLabel(row_days, text="days_back").pack(side="left", padx=(0, 6))
        self.days_back = ctk.CTkEntry(row_days, width=70)
        self.days_back.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(row_days, text="days_forward").pack(side="left", padx=(0, 6))
        self.days_forward = ctk.CTkEntry(row_days, width=70)
        self.days_forward.pack(side="left")

        # Row 2 — email + Outlook auth buttons
        row_email = ctk.CTkFrame(left, fg_color="transparent")
        row_email.grid(row=1, column=0, columnspan=2, padx=4, pady=3, sticky="ew")
        row_email.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(row_email, text="email").grid(row=0, column=0, padx=(0, 6), sticky="w")
        self.email = ctk.CTkEntry(row_email)
        self.email.grid(row=0, column=1, padx=(0, 8), sticky="ew")
        self.email.bind("<FocusOut>", lambda _e: self._refresh_outlook_login_buttons())
        outlook_btns = ctk.CTkFrame(row_email, fg_color="transparent")
        outlook_btns.grid(row=0, column=2, sticky="e")
        self.login_btn = ctk.CTkButton(
            outlook_btns, text="Login to Outlook", width=140, command=self._on_login
        )
        self.check_outlook_btn = ctk.CTkButton(
            outlook_btns,
            text="Check Outlook auth",
            width=150,
            command=self._on_check_outlook,
        )
        self.remove_outlook_btn = ctk.CTkButton(
            outlook_btns,
            text="Remove Outlook credential",
            width=190,
            fg_color=ERROR_COLOR,
            hover_color="#a32f2f",
            command=self._on_remove_outlook,
        )
        self._outlook_auth_frame = outlook_btns

        # Row 3 — server + username
        row_srv = ctk.CTkFrame(left, fg_color="transparent")
        row_srv.grid(row=2, column=0, columnspan=2, padx=4, pady=3, sticky="ew")
        row_srv.grid_columnconfigure(1, weight=1)
        row_srv.grid_columnconfigure(3, weight=1)
        ctk.CTkLabel(row_srv, text="server").grid(row=0, column=0, padx=(0, 6), sticky="w")
        self.server = ctk.CTkEntry(row_srv)
        self.server.grid(row=0, column=1, padx=(0, 12), sticky="ew")
        ctk.CTkLabel(row_srv, text="username").grid(row=0, column=2, padx=(0, 6), sticky="w")
        self.username = ctk.CTkEntry(row_srv, placeholder_text="empty = email")
        self.username.grid(row=0, column=3, sticky="ew")

        # Row 4 — auth + verify SSL
        row_auth = ctk.CTkFrame(left, fg_color="transparent")
        row_auth.grid(row=3, column=0, columnspan=2, padx=4, pady=3, sticky="w")
        ctk.CTkLabel(row_auth, text="auth").pack(side="left", padx=(0, 6))
        self.auth = ctk.CTkOptionMenu(row_auth, values=["ntlm", "basic"], width=100)
        self.auth.pack(side="left", padx=(0, 16))
        self.verify_ssl = ctk.CTkCheckBox(row_auth, text="verify SSL")
        self.verify_ssl.pack(side="left")

        # Row 5 — Save config + Import credentials only
        row_save = ctk.CTkFrame(left, fg_color="transparent")
        row_save.grid(row=4, column=0, columnspan=2, padx=4, pady=(8, 3), sticky="w")
        self.save_btn = ctk.CTkButton(
            row_save, text="Save config", width=120, command=self._save_config
        )
        self.save_btn.pack(side="left", padx=(0, 8))
        self.import_btn = ctk.CTkButton(
            row_save,
            text="Import credentials",
            width=150,
            command=self._on_import_credentials,
        )
        self.import_btn.pack(side="left")

        # Vertical divider
        divider = ctk.CTkFrame(top, width=2, fg_color=("gray65", "gray40"))
        divider.grid(row=0, column=1, sticky="ns", padx=6, pady=12)
        divider.grid_propagate(False)

        # —— Section 2 (right): Google session ——
        right = ctk.CTkFrame(top, fg_color="transparent")
        right.grid(row=0, column=2, padx=(4, 8), pady=8, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right, text="Google session", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=6, pady=(4, 8), sticky="w")

        row_gcal = ctk.CTkFrame(right, fg_color="transparent")
        row_gcal.grid(row=1, column=0, padx=6, pady=4, sticky="ew")
        row_gcal.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(row_gcal, text="Google calendar").grid(
            row=0, column=0, padx=(0, 6), sticky="w"
        )
        self.google_calendar = ctk.CTkEntry(row_gcal)
        self.google_calendar.grid(row=0, column=1, sticky="ew")

        google_setup = ctk.CTkFrame(right, fg_color="transparent")
        google_setup.grid(row=2, column=0, padx=6, pady=4, sticky="w")
        self.setup_btn = ctk.CTkButton(
            google_setup, text="Setup Google", width=130, command=self._on_setup_google
        )
        self.setup_btn.pack(side="left", padx=(0, 4))
        self.remove_google_btn = ctk.CTkButton(
            google_setup,
            text="Remove Google auth",
            width=160,
            fg_color=ERROR_COLOR,
            hover_color="#a32f2f",
            command=self._on_remove_google,
        )
        self._google_inline_frame = google_setup

        row_priv = ctk.CTkFrame(right, fg_color="transparent")
        row_priv.grid(row=3, column=0, padx=6, pady=4, sticky="w")
        ctk.CTkLabel(row_priv, text="privacy").pack(side="left", padx=(0, 6))
        self.privacy = ctk.CTkOptionMenu(row_priv, values=["full", "busy"], width=100)
        self.privacy.pack(side="left")

        google_btns = ctk.CTkFrame(right, fg_color="transparent")
        google_btns.grid(row=4, column=0, padx=6, pady=(8, 4), sticky="w")
        self.check_google_btn = ctk.CTkButton(
            google_btns,
            text="Check Google auth",
            width=150,
            command=self._on_check_google,
        )
        self.check_google_btn.pack(side="left", padx=(0, 8), pady=4)
        self.reauth_btn = ctk.CTkButton(
            google_btns, text="Reauth Google", width=150, command=self._on_reauth
        )
        self.reauth_btn.pack(side="left", padx=0, pady=4)
        self._google_auth_frame = google_btns

        # ~4+ lines visible; panes grow with the window and scroll
        _pane_height = 100

        events_frame = ctk.CTkFrame(self)
        events_frame.grid(row=2, column=0, padx=16, pady=(4, 6), sticky="nsew")
        events_frame.grid_columnconfigure(0, weight=1)
        events_frame.grid_rowconfigure(1, weight=1)

        events_header = ctk.CTkFrame(events_frame, fg_color="transparent")
        events_header.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="ew")
        events_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            events_header, text="Outlook events", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, sticky="w")
        self.clear_events_btn = ctk.CTkButton(
            events_header, text="Clear", width=80, command=self._on_clear_events
        )
        self.clear_events_btn.grid(row=0, column=1, sticky="e")
        self.events_box = ctk.CTkTextbox(
            events_frame,
            font=ctk.CTkFont(family="Menlo", size=12),
            height=_pane_height,
            wrap="none",
        )
        self.events_box.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")
        self.events_box.insert(
            "1.0",
            "Click “Show events from outlook” to load events from Outlook/Exchange.\n",
        )
        self.events_box.configure(state="disabled")

        logs_frame = ctk.CTkFrame(self)
        logs_frame.grid(row=3, column=0, padx=16, pady=(4, 6), sticky="nsew")
        logs_frame.grid_columnconfigure(0, weight=1)
        logs_frame.grid_rowconfigure(1, weight=1)

        logs_header = ctk.CTkFrame(logs_frame, fg_color="transparent")
        logs_header.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="ew")
        logs_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            logs_header, text="Logs", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, sticky="w")
        self.clear_logs_btn = ctk.CTkButton(
            logs_header, text="Clear", width=80, command=self._on_clear_logs
        )
        self.clear_logs_btn.grid(row=0, column=1, sticky="e")
        self.logs = ctk.CTkTextbox(
            logs_frame,
            font=ctk.CTkFont(family="Menlo", size=12),
            height=_pane_height,
        )
        self.logs.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")
        self._init_log_tags()

        # Stop + Reset (right end)
        row1 = ctk.CTkFrame(self)
        row1.grid(row=4, column=0, padx=16, pady=(0, 2), sticky="ew")
        self.stop_btn = ctk.CTkButton(
            row1,
            text="Stop",
            width=90,
            fg_color=ERROR_COLOR,
            hover_color="#a32f2f",
            command=self._on_stop,
            state="disabled",
        )
        self.stop_btn.pack(side="right", padx=4, pady=6)
        self.reset_btn = ctk.CTkButton(
            row1,
            text="Reset credentials…",
            width=160,
            fg_color=ERROR_COLOR,
            hover_color="#a32f2f",
            command=self._on_reset,
        )
        # Packed by _refresh_reset_button when any credentials exist.

        # Row 2 — sync + list calendars
        row2 = ctk.CTkFrame(self)
        row2.grid(row=5, column=0, padx=16, pady=2, sticky="ew")
        self.sync_btn = self._lead_button(row2, "Sync", self._on_sync, width=100)
        self.sync_btn.configure(state="disabled")
        self.sync_btn.pack(side="left", padx=4, pady=6)
        self.dry_btn = ctk.CTkButton(
            row2, text="Sync dry-run", width=110, command=self._on_sync_dry
        )
        self.dry_btn.pack(side="left", padx=4, pady=6)
        self.list_cal_btn = ctk.CTkButton(
            row2, text="List calendars", width=130, command=self._on_list_calendars
        )
        self.list_cal_btn.pack(side="left", padx=4, pady=6)

        # Row 3 — Outlook fetch / encrypted hand-off
        row3 = ctk.CTkFrame(self)
        row3.grid(row=6, column=0, padx=16, pady=2, sticky="ew")
        self.get_btn = self._lead_button(
            row3, "Show events from outlook", self._on_get, width=200
        )
        self.get_btn.pack(side="left", padx=4, pady=6)
        self.store_btn = ctk.CTkButton(
            row3,
            text="Get from outlook and Store encrypted",
            width=260,
            command=self._on_store,
        )
        self.store_btn.pack(side="left", padx=4, pady=6)
        self.sync_stored_btn = ctk.CTkButton(
            row3,
            text="Sync from encrypted file",
            width=180,
            command=self._on_sync_stored,
        )
        self.sync_stored_btn.pack(side="left", padx=4, pady=6)

        # Row 4 — schedule
        row4 = ctk.CTkFrame(self)
        row4.grid(row=7, column=0, padx=16, pady=(2, 4), sticky="ew")
        self.sched_btn = ctk.CTkButton(
            row4, text="Install schedule", width=140, command=self._on_install_schedule
        )
        self.sched_btn.pack(side="left", padx=4, pady=6)
        self.unsched_btn = ctk.CTkButton(
            row4, text="Uninstall schedule", width=150, command=self._on_uninstall_schedule
        )
        self.unsched_btn.pack(side="left", padx=4, pady=6)

        self._action_buttons = [
            self.get_btn,
            self.sync_btn,
            self.dry_btn,
            self.list_cal_btn,
            self.login_btn,
            self.check_outlook_btn,
            self.remove_outlook_btn,
            self.setup_btn,
            self.remove_google_btn,
            self.save_btn,
            self.import_btn,
            self.store_btn,
            self.sync_stored_btn,
            self.sched_btn,
            self.unsched_btn,
            self.data_btn,
            self.reset_btn,
            self.clear_events_btn,
            self.clear_logs_btn,
        ]

        self.status = ctk.CTkLabel(self, text="", anchor="w")
        self.status.grid(row=8, column=0, padx=16, pady=(0, 16), sticky="ew")

    def _refresh_auth_buttons(self) -> None:
        self._refresh_outlook_login_buttons()
        self._refresh_google_auth_buttons()
        self._refresh_reset_button()

    def _has_any_credentials(self) -> bool:
        from . import ews

        if CREDENTIALS_PATH.exists() or TOKEN_PATH.exists():
            return True
        return ews.has_stored_password(self.email.get().strip())

    def _refresh_reset_button(self) -> None:
        self.reset_btn.pack_forget()
        if self._has_any_credentials():
            # Left of Stop (packed right-to-left: Stop first, then Reset beside it).
            self.reset_btn.pack(side="right", padx=4, pady=6)
            self.reset_btn.configure(state="disabled" if self._busy else "normal")

    def _refresh_google_auth_buttons(self) -> None:
        setup_done = CREDENTIALS_PATH.exists()
        has_token = TOKEN_PATH.exists()
        self.remove_google_btn.pack_forget()
        if setup_done:
            self.setup_btn.configure(text="Google already set up")
            self.remove_google_btn.pack(side="left", padx=4)
        else:
            self.setup_btn.configure(text="Setup Google")
        # First sign-in creates token.json; later uses reauth the same way.
        self.reauth_btn.configure(
            text="Sign in to Google" if setup_done and not has_token else "Reauth Google"
        )
        # Check / Reauth live in the right section; enable when credentials exist.
        state = "disabled" if (self._busy or not setup_done) else "normal"
        self.check_google_btn.configure(state=state)
        self.reauth_btn.configure(state=state)

    def _refresh_outlook_login_buttons(self) -> None:
        from . import ews

        email = self.email.get().strip()
        has_pw = ews.has_stored_password(email)
        self.login_btn.pack_forget()
        self.check_outlook_btn.pack_forget()
        self.remove_outlook_btn.pack_forget()
        if has_pw:
            self.check_outlook_btn.pack(side="left", padx=4, pady=2)
            self.remove_outlook_btn.pack(side="left", padx=4, pady=2)
        else:
            self.login_btn.pack(side="left", padx=4, pady=2)

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
        self.privacy.set(str(data.get("privacy", "full")))
        self.email.delete(0, "end")
        self.email.insert(0, str(ews.get("email", "")))
        self.server.delete(0, "end")
        self.server.insert(0, str(ews.get("server", "mail.digikala.com")))
        self.username.delete(0, "end")
        # Keep empty when unset or when it was previously auto-filled as email.
        stored_user = str(ews.get("username", "")).strip()
        email_val = str(ews.get("email", "")).strip()
        if stored_user and stored_user != email_val:
            self.username.insert(0, stored_user)
        self.auth.set(str(ews.get("auth", "ntlm")))
        if ews.get("verify_ssl", False):
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
        self._refresh_auth_buttons()
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
            self.check_google_btn.configure(state="disabled")
            self.reauth_btn.configure(state="disabled")
        else:
            self.sync_btn.configure(state="normal" if self._events else "disabled")
            self._refresh_google_auth_buttons()
            self._refresh_reset_button()

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

    def _confirm(self, title: str, message: str) -> bool:
        """Modal Confirm / Cancel dialog (no typing required). Must run on the UI thread."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.transient(self)
        dialog.resizable(False, False)
        dialog.grab_set()

        result = {"ok": False}

        body = ctk.CTkFrame(dialog, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(18, 8))
        ctk.CTkLabel(
            body,
            text=message,
            justify="left",
            wraplength=420,
            anchor="w",
        ).pack(anchor="w")

        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(fill="x", padx=20, pady=(8, 18))

        def on_cancel() -> None:
            result["ok"] = False
            dialog.destroy()

        def on_confirm() -> None:
            result["ok"] = True
            dialog.destroy()

        ctk.CTkButton(buttons, text="Cancel", width=100, command=on_cancel).pack(
            side="right", padx=(8, 0)
        )
        ctk.CTkButton(
            buttons,
            text="Confirm",
            width=100,
            fg_color=ERROR_COLOR,
            hover_color="#a32f2f",
            command=on_confirm,
        ).pack(side="right")

        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        dialog.update_idletasks()
        # Center over the main window.
        x = self.winfo_rootx() + (self.winfo_width() - dialog.winfo_reqwidth()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dialog.winfo_reqheight()) // 2
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        dialog.wait_window()
        return bool(result["ok"])

    def _confirm_from_worker(self, title: str, message: str) -> bool:
        """Show Confirm/Cancel from a background thread; blocks until answered."""
        box: dict[str, bool] = {"ok": False}
        done = threading.Event()

        def on_main() -> None:
            try:
                box["ok"] = self._confirm(title, message)
            finally:
                done.set()

        self.after(0, on_main)
        done.wait()
        return bool(box["ok"])

    def _sign_in_google_if_needed(self, *, from_worker: bool = False) -> tuple[bool, str]:
        """Create token.json via browser OAuth when credentials exist but token does not."""
        if not CREDENTIALS_PATH.exists():
            return False, "Missing credentials.json — Setup Google first."
        if TOKEN_PATH.exists():
            return True, "token.json already present"
        ask = self._confirm_from_worker if from_worker else self._confirm
        if not ask(
            "Sign in to Google",
            "credentials.json is ready, but token.json is not created yet.\n\n"
            "Sign in with your Gmail now to create token.json?\n"
            "(If company VPN blocks Google, use a personal VPN briefly.)",
        ):
            return False, "Sign-in skipped — click Sign in to Google when ready."
        return reauth_google(log=self._gui_log)

    def _on_clear_events(self) -> None:
        if not self._confirm("Clear Outlook events", "Clear the Outlook events list?"):
            return
        self._events = []
        self._set_events_text(
            [
                "Click “Show events from outlook” to load events from Outlook/Exchange.",
            ]
        )
        self.sync_btn.configure(state="disabled")
        self._set_status("Outlook events cleared.", "info")

    def _on_clear_logs(self) -> None:
        if not self._confirm("Clear logs", "Clear all log messages?"):
            return
        self.logs.configure(state="normal")
        self.logs.delete("1.0", "end")
        self.logs.configure(state="normal")
        self._set_status("Logs cleared.", "info")

    def _on_stop(self) -> None:
        if not self._busy:
            self._set_status("Nothing in progress to stop.", "info")
            return
        if not self._confirm(
            "Stop in-progress actions?",
            "Stop all in-progress work?\n\n"
            "Get / Sync / Store will cancel after the current step.\n"
            "Other actions may finish their current network call first.",
        ):
            return
        self._cancel.set()
        self._append_log(
            "info",
            "Stop confirmed — cancelling in-progress actions after the current step…",
        )
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
                self._refresh_outlook_login_buttons()
                self._refresh_reset_button()
                self._set_status(msg, "success" if ok else "error")

            self.after(0, done)

        self._run_async(work)

    def _on_check_outlook(self) -> None:
        if not self._save_config():
            return

        def work() -> None:
            ok, msg = check_outlook_auth(log=self._gui_log)

            def done() -> None:
                self._set_status(msg, "success" if ok else "error")

            self.after(0, done)

        self._run_async(work)

    def _on_remove_outlook(self) -> None:
        email = self.email.get().strip()
        if not email:
            self._set_status("Set an email first.", "error")
            return
        if not self._confirm(
            "Remove Outlook credential",
            f"Remove the saved Exchange password for {email} from the OS keyring?\n\n"
            "You will need to use Login to Outlook again before syncing.",
        ):
            self._set_status("Remove cancelled.", "info")
            return
        from . import ews

        if ews.clear_password(email):
            self._append_log("success", f"Removed Exchange password for {email}")
            self._set_status("Outlook credential removed.", "success")
        else:
            self._append_log("info", f"No Exchange password found for {email}")
            self._set_status("No Outlook credential was stored.", "info")
        self._refresh_outlook_login_buttons()
        self._refresh_reset_button()

    def _on_check_google(self) -> None:
        if not self._save_config():
            return

        def work() -> None:
            ok, msg = check_google_auth(log=self._gui_log)
            if (not ok) and CREDENTIALS_PATH.exists() and not TOKEN_PATH.exists():
                sign_ok, sign_msg = self._sign_in_google_if_needed(from_worker=True)
                if sign_ok:
                    ok, msg = check_google_auth(log=self._gui_log)
                else:
                    msg = sign_msg

            def done() -> None:
                self._refresh_google_auth_buttons()
                self._set_status(msg, "success" if ok else "error")

            self.after(0, done)

        self._run_async(work)

    def _on_remove_google(self) -> None:
        if not self._confirm(
            "Remove Google auth",
            "Remove credentials.json and token.json?\n\n"
            "The Google Calendar is NOT deleted (use Reset for that).\n"
            "You will need Setup Google / Import credentials again before syncing.",
        ):
            self._set_status("Remove cancelled.", "info")
            return

        def work() -> None:
            ok, msg = remove_google_credentials(confirmed=True, log=self._gui_log)

            def done() -> None:
                self._refresh_google_auth_buttons()
                self._refresh_reset_button()
                self.sync_btn.configure(state="disabled")
                self._set_status(
                    "Google credentials removed." if ok else msg,
                    "success" if ok else "error",
                )

            self.after(0, done)

        self._run_async(work)

    def _on_reauth(self) -> None:
        if not CREDENTIALS_PATH.exists():
            self._set_status("Missing credentials.json — Setup Google first.", "error")
            return
        first_login = not TOKEN_PATH.exists()
        title = "Sign in to Google" if first_login else "Reauth Google"
        body = (
            "This opens a browser to sign in and create token.json.\n"
            "If the company VPN blocks Google, use a personal VPN briefly."
            if first_login
            else "This opens a browser to sign in to Google again.\n"
            "If the company VPN blocks Google, use a personal VPN briefly."
        )
        if not self._confirm(title, body):
            return

        def work() -> None:
            ok, msg = reauth_google(log=self._gui_log)

            def done() -> None:
                self._refresh_google_auth_buttons()
                self._refresh_reset_button()
                self._set_status(msg, "success" if ok else "error")

            self.after(0, done)

        self._run_async(work)

    def _on_reset(self) -> None:
        cal_name = "Work (Outlook)"
        email = self.email.get().strip() or "(from config)"
        try:
            settings = load_settings()
            cal_name = settings.google_calendar
            if settings.ews and settings.ews.email:
                email = settings.ews.email
        except ConfigError:
            settings = None

        warning = (
            "This permanently removes:\n\n"
            f"• Google Calendar named “{cal_name}”\n"
            "• credentials.json and token.json (Google OAuth)\n"
            "• events.enc (encrypted Outlook snapshot), if present\n"
            f"• Exchange password for {email} from the OS keyring\n\n"
            "config.yaml is NOT deleted."
        )
        if not self._confirm("Reset credentials", warning):
            self._set_status("Reset cancelled.", "info")
            return

        def work() -> None:
            result = reset_credentials_and_calendar(
                settings,
                delete_google_calendar=True,
                confirmed=True,
                log=self._gui_log,
            )

            def done() -> None:
                self._refresh_auth_buttons()
                self.sync_btn.configure(state="disabled")
                self._set_status(
                    "Reset finished." if result.ok else result.message,
                    "success" if result.ok else "error",
                )
                if result.ok:
                    messagebox.showinfo("Reset finished", result.message, parent=self)

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
            return self._confirm_from_worker(title, message)

        def work() -> None:
            try:
                ok = walk_google_oauth_gui(ask_continue=ask_continue, log=self._gui_log)
                if ok and CREDENTIALS_PATH.exists() and not TOKEN_PATH.exists():
                    sign_ok, sign_msg = self._sign_in_google_if_needed(from_worker=True)
                    if sign_ok:
                        msg = "Google setup finished — token.json created."
                    else:
                        msg = (
                            "credentials.json is ready. "
                            f"{sign_msg}"
                        )
                elif ok and CREDENTIALS_PATH.exists():
                    msg = "Google setup finished."
                else:
                    msg = "Google setup incomplete — use Import credentials if needed."
                    ok = False
            except Exception as exc:
                ok = False
                msg = f"Google setup failed: {exc}"
                self._gui_log("error", msg)

            def done() -> None:
                self._refresh_google_auth_buttons()
                self._refresh_reset_button()
                self._set_status(
                    msg,
                    "success" if CREDENTIALS_PATH.exists() and TOKEN_PATH.exists() else (
                        "success" if CREDENTIALS_PATH.exists() else "error"
                    ),
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
        self._refresh_google_auth_buttons()
        self._refresh_reset_button()
        if not TOKEN_PATH.exists():
            if self._confirm(
                "Sign in to Google",
                "credentials.json saved.\n\n"
                "Sign in with your Gmail now to create token.json?\n"
                "(If company VPN blocks Google, use a personal VPN briefly.)",
            ):
                def work() -> None:
                    ok, msg = reauth_google(log=self._gui_log)

                    def done() -> None:
                        self._refresh_google_auth_buttons()
                        self._refresh_reset_button()
                        self._set_status(msg, "success" if ok else "error")

                    self.after(0, done)

                self._run_async(work)
                return
            self._set_status(
                "credentials.json saved — click Sign in to Google to create token.json.",
                "info",
            )
            return
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
