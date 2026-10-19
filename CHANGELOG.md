# Changelog

All notable changes are documented here.  
GitHub Releases should use the same version as the git tag: `vMAJOR.MINOR.PATCH` (see `VERSION`).

## 0.8.0 — 2026-10-19

### Added

- `./scripts/release_macos.sh` — ask whether to release the current `VERSION` or an existing previous tag; pick from the 5 latest tags; warn if `v$VERSION` was already tagged and ask whether to continue; build release notes from CHANGELOG between a chosen since-tag and the release version; build the DMG; push the tag if needed; create a GitHub Release with the DMG (`gh` required)

### Changed

- First-time FA/EN guides rewritten around the **DMG + GUI** flow: Privacy & Security **Open Anyway**, Keychain **Always Allow**, company vs personal VPN, Outlook login first, Google Setup with per-step screenshots, Show events / Sync, and Install schedule (e.g. every 30m)
- README first-time section and macOS DMG install notes point at that GUI walkthrough

## 0.7.0 — 2026-10-18

### Added

- Guided Google setup with per-step screenshots (cursor + click/type callouts), visible reopenable URLs (**Open link again**), and resume via `google_setup_progress.json`
- GUI Confirm dialogs use selectable/copyable text
- Sync calendar gets a default **15-minute** popup reminder (new and existing Work calendars)
- Schedule interval choices: `15m`, `30m`, `1h`, `3h`, `6h`, `12h` (CLI `--every`, GUI dropdown, `schedule_every` in config)
- `python -m syncer sync-scheduled` for background runs; macOS notification when a scheduled sync fails

### Changed

- Background schedule now invokes `sync-scheduled` instead of plain `sync`
- Google setup CLI/GUI share structured step metadata

## 0.6.0 — 2026-10-18

### Added

- `python -m syncer reset` — delete the Google sync calendar and wipe Outlook/Google credentials & tokens (type `DELETE` to confirm; `--yes` / `--keep-calendar` optional)
- GUI **Reset credentials…** (beside **Stop** when any credentials exist) with Confirm / Cancel (does not delete `config.yaml`)
- GUI top: two sections with a vertical divider — left config (days, email+Outlook auth, server/username, auth/SSL, Save/Import); right Google session (calendar name, Setup/Remove, privacy, Check/Reauth); **Open data folder** beside the data-folder path under the title
- **List calendars** on the Sync / Sync dry-run row
- After Google setup: **Remove Google auth** (confirm); right section **Check Google auth** / **Reauth Google**
- Beside email: **Login to Outlook** or **Check Outlook auth** + **Remove Outlook credential**
- **Stop** asks for confirmation, then cancels in-progress Get / Sync / Store after the current step
- GUI **Clear** on the Outlook events and Logs panes (with Confirm / Cancel)
- GUI confirmations use **Confirm** / **Cancel** only (no typing `DELETE` or other text prompts)
- After Setup Google / Import credentials (and when Check Google auth finds no token), GUI offers browser sign-in to create `token.json`; button shows **Sign in to Google** until a token exists

### Changed

- Default `privacy` is now `full` (was `busy`)
- Default Exchange host is now `mail.digikala.com`
- Default `ews.verify_ssl` is now `false` (GUI checkbox starts unticked)
- macOS app display name is **Outlook to Google Calendar Syncer** (window title, `.app` bundle, and DMG)
- GUI layout: fixed overlapping title / data-folder label; regrouped action buttons; Outlook events + Logs panes show ≥4 lines and scroll
- Teal lead color on Sync and “Show events from outlook” rows only
- “Show events from outlook” / “Get from outlook and Store encrypted” / “Sync from encrypted file”
- Setup Google becomes **Google already set up** when `credentials.json` exists
- Old template configs still on `mail.company.com` are migrated to the new Digikala defaults on launch
- `ews.username` stays empty in config/UI by default (Exchange uses email when blank)
- CLI: `tokens` / `check` → `check-outlook-auth` / `check-google-auth`
- CLI: `login` → `login-to-outlook`; `get` → `show-outlook-events`

## 0.5.0 — 2026-10-18

### Added

- Self-contained **macOS `.app` + `.dmg`** build (`./scripts/build_macos_dmg.sh`) — users do not need Python installed
- Frozen app entry (`syncer.app_entry`): double-click opens the GUI; CLI args still work for launchd / Terminal
- GUI covers all main commands: Get, Sync, dry-run, Store encrypted, Sync from file, tokens, login, reauth, list calendars, check, install/uninstall schedule, Setup Google, Open data folder
- User data for the frozen app lives in `~/Library/Application Support/outlook-to-gmail-calendar-syncer/`

### Changed

- `ROOT` / config / credentials / `events.enc` resolve via Application Support when frozen; project folder in development
- launchd / Task Scheduler / systemd call the frozen binary with `sync` when packaged

## 0.4.0 — 2026-10-12

### Added

- `python -m syncer store` — fetch Outlook/Exchange events and save them to a password-encrypted file (`events.enc` by default)
- `python -m syncer sync-stored` — decrypt that file later and sync to Google Calendar (no Outlook/VPN needed for the fetch step)
- Optional `--dry-run` for `sync-stored`; override paths with `-o` / `-i`; password via prompt or `SYNCER_STORE_PASSWORD`
- First-time setup guides: [docs/FIRST_TIME_EN.md](docs/FIRST_TIME_EN.md) and [docs/FIRST_TIME_FA.md](docs/FIRST_TIME_FA.md) (linked from the README)

### Notes

- Existing `get` / `sync` / schedule behaviour is unchanged
- Encryption uses Fernet (AES) with PBKDF2-SHA256; keep the password — lost passwords cannot recover the file

## 0.3.0 — 2026-10-11

### Added

- **Linux and Windows** support alongside macOS (EWS + Google; `source: apple` remains macOS-only)
- Portable timezone detection via `tzlocal` when `timezone` is empty (macOS still uses Foundation)
- `install-schedule` / `uninstall-schedule` for Windows Task Scheduler and Linux systemd `--user`
- Platform-marked dependencies: pyobjc (darwin only), `tzdata` (Windows), SecretStorage (Linux)

### Changed

- CLI/docs refer to the OS keyring instead of Keychain-only wording
- GUI missing-Tk message includes Windows and Linux install hints

### Notes

- macOS launchd, EventKit (`source: apple`), and Foundation timezone detection are unchanged
- On Linux/Windows use `source: ews`; headless Linux may need `EWS_PASSWORD` if no Secret Service is available

## 0.2.0 — 2026-09-23

### Added

- **Desktop GUI** (`python -m syncer gui`) with CustomTkinter (Homebrew: `brew install python-tk@3.13`):
  - System light/dark appearance
  - Config form (`days_back`, `days_forward`, email, server, privacy, …) saved to `config.yaml`
  - **Get** loads Outlook events; **Sync** enabled after a successful Get
  - **Stop** cancels an in-progress Get/Sync between steps
  - Logs: green success / light red errors; status line for outcome
  - Check tokens, Login Exchange, Reauth Google, Setup Google, Import credentials
- Shared library API (`syncer.api`: `get_events`, `run_sync`, …) used by CLI and GUI
- First-run bootstrap (`syncer.bootstrap`): creates `config.yaml` if missing; guides creation of `credentials.json`; `token.json` after first Google sign-in
- `python -m syncer get` — list Outlook events in the date window
- Numbered interactive menu: `python -m syncer`
- `python -m syncer tokens` / `reauth-google`
- Project version in `VERSION` and `python -m syncer --version`

### Fixed

- Google `invalid_grant` / expired refresh token recovers with re-auth instead of crashing
- SSL / network errors to Google show a short VPN guide
- Sync fails fast on VPN hangs (Google ~30s, Exchange ~45s) with step progress
- Exchange fetch uses `.only(...)`; notes skipped when `privacy: busy`

### Notes

- Exchange needs the company VPN; Google OAuth/Calendar need the public internet (or split tunneling)
- A real `credentials.json` still requires Google Cloud Desktop OAuth (Setup Google / import); the app cannot invent valid Google client secrets

## 0.1.0 — 2026-09-09

- Initial release: one-way Outlook/Exchange → Google Calendar sync on macOS
- EWS source without Apple Mail
- Interactive `setup` wizard for Google Cloud OAuth / Calendar API
- Optional launchd schedule every 15 minutes
