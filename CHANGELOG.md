# Changelog

All notable changes are documented here.  
GitHub Releases should use the same version as the git tag: `vMAJOR.MINOR.PATCH` (see `VERSION`).

## Unreleased

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
