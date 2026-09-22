# Changelog

## Unreleased

### Added

- **Interactive numbered menu** — run with no arguments:

  ```bash
  python -m syncer
  ```

  Then enter a number:

  | Number | Action |
  |---:|---|
  | `1` | setup |
  | `2` | setup --google-only |
  | `3` | login |
  | `4` | reauth-google |
  | `5` | tokens |
  | `6` | list-calendars |
  | `7` | check |
  | `8` | sync --dry-run |
  | `9` | sync |
  | `10` | install-schedule |
  | `11` | uninstall-schedule |
  | `0` | quit |

- `python -m syncer tokens` — check whether Exchange and Google logins/tokens are still valid.
- `python -m syncer reauth-google` — delete `token.json` and sign in to Google again.

### Fixed

- Google `invalid_grant` / expired refresh token no longer crashes `sync` or `check`. The tool clears the old token and opens a browser sign-in instead (common while the OAuth app is left in Testing; tokens last ~7 days).
- SSL / network errors talking to `oauth2.googleapis.com` (often company VPN) show a short guide instead of a long traceback. Interactive menu catches command failures and returns to the prompt.
- Sync no longer hangs forever when Google is unreachable: Google HTTP timeout is 30s; Exchange EWS timeout is 45s. Progress lines show which step is running.
- Exchange event fetch uses `.only(...)` so body/notes are not lazy-loaded one-by-one (that used to stall on slow servers). Notes are skipped entirely when `privacy: busy`.

### Notes

- **VPN tip:** Exchange needs the company VPN; Google OAuth / Calendar API need the public internet. If sync hangs or times out after “Found N event(s)”, disconnect VPN briefly for Google, or ask IT for split tunneling.

## 0.1.0 — 2026-09-09

- Initial release: one-way Outlook/Exchange → Google Calendar sync on macOS.
- EWS source (`mail.company.com`) without Apple Mail.
- Interactive `setup` wizard for Google Cloud OAuth / Calendar API.
- Optional launchd schedule every 15 minutes.
