# outlook-to-gmail-calendar-syncer

One-way copy of an **Outlook / Exchange** calendar into a **dedicated Google calendar**. Your computer is the bridge: it reads Exchange (often only reachable on a company VPN) and writes copies to Google.

Works on **macOS**, **Windows**, and **Linux**. Use `source: ews` (recommended everywhere). `source: apple` (Calendar.app / EventKit) is **macOS only**.

Apple Mail is not required. Attendees are not copied, so coworkers do not get extra invites.

This is a **personal** tool. Check with IT before copying a work calendar to a personal Google account.

## First-time guides

Ordinary Mac users: install the DMG, then follow the GUI walkthrough (Outlook login → Google setup with screenshots → sync → schedule):

- **English:** [docs/FIRST_TIME_EN.md](docs/FIRST_TIME_EN.md)
- **فارسی:** [docs/FIRST_TIME_FA.md](docs/FIRST_TIME_FA.md)

## macOS app (no Python required)

Ordinary Mac users can install a self-contained app from a DMG (Python is bundled inside):

1. On a Mac with this repo + Python 3.11+, build once:

```bash
./scripts/build_macos_dmg.sh
```

2. Share `dist/Outlook-to-Google-Calendar-Syncer-<version>.dmg`.
3. User opens the DMG → drags **Outlook to Google Calendar Syncer.app** to Applications → double-clicks.
4. If macOS blocks the first launch: **System Settings → Privacy & Security → Open Anyway**. Keychain may ask for the Mac password — choose **Always Allow** when offered.
5. All setup / get / sync / store / schedule actions are buttons in the app (see the first-time guides above).

App data (config, Google tokens, encrypted store) goes to:

`~/Library/Application Support/outlook-to-gmail-calendar-syncer/`

Optional CLI using the same binary (still no system Python):

```bash
/Applications/Outlook\ to\ Google\ Calendar\ Syncer.app/Contents/MacOS/OutlookToGoogleCalendarSyncer sync --dry-run
```

For public downloads, sign and notarize the app/DMG with an Apple Developer ID (the build script prints example commands).

## Quick start

Python **3.11+**.

```bash
git clone https://github.com/hamidhandid/outlook-to-gmail-calendar-syncer.git
cd outlook-to-gmail-calendar-syncer
python3 -m venv .venv
```

**macOS / Linux**

```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m syncer setup
```

**Windows** (Command Prompt or PowerShell)

```bat
.venv\Scripts\activate
pip install -r requirements.txt
python -m syncer setup
```

### GUI (recommended for ordinary users)

```bash
# macOS Homebrew Python needs Tk once:
brew install python-tk@3.13

# Linux (Debian/Ubuntu):
#   sudo apt install python3-tk
# Windows: use the python.org installer with Tcl/Tk enabled

pip install -r requirements.txt   # includes customtkinter
python -m syncer gui
```

The desktop app follows the **system light/dark** theme and uses the same core as the CLI:

1. Fill config fields on the left → **Save config** (writes `config.yaml`)
2. Top-right: **Outlook** (Login / Check auth) and **Google** (Setup / Check auth / Reauth)
3. **Show events from outlook** — loads Outlook events into the list (VPN on)
4. **Sync** — enabled after a successful Get; copies those events to Google

**Logs** use green for success and a light red for errors. The status line under the buttons shows whether the last action succeeded.

### Terminal menu

```bash
python -m syncer
```

Then type a number (for example `11` for sync, `1` for gui, `0` to quit).

## Setup wizard (Google Cloud)

```bash
python -m syncer setup
# or only Google OAuth:
python -m syncer setup --google-only
```

1. Create a Google Cloud project  
2. Enable the **Google Calendar API**  
3. OAuth consent screen: **External** + yourself as a test user  
4. Create a **Desktop** OAuth client → save as `credentials.json`  
5. Write / confirm `config.yaml`  

If Google says the app is unverified: **Advanced → Go to … (unsafe)**. While the app stays in **Testing**, Google may expire the login after **7 days** — run `python -m syncer reauth-google` or use **Reauth Google** in the GUI.

## Typical CLI flow (VPN on)

```bash
python -m syncer login-to-outlook
python -m syncer check-outlook-auth
python -m syncer check-google-auth
python -m syncer show-outlook-events   # list events in the configured date window
python -m syncer sync --dry-run
python -m syncer sync
# optional offline path (company VPN for store, Google later without Outlook):
# python -m syncer store
# python -m syncer sync-stored
python -m syncer install-schedule --every 15m   # or 30m / 1h / 3h / 6h / 12h
```

Events appear in Google Calendar under the name you chose (default **Work (Outlook)**).

### Encrypted offline hand-off

Use this when you can reach Exchange now but want to sync to Google later (or on another network):

1. With company VPN: `python -m syncer store` — prompts for a password and writes `events.enc` (gitignored).
2. Later, with Google reachable: `python -m syncer sync-stored` — same password, then syncs to Google.

Optional: `-o` / `-i` for a custom path, `--dry-run` on `sync-stored`, or `SYNCER_STORE_PASSWORD` to avoid the prompt. Existing `show-outlook-events` / `sync` are unchanged.

## Config

`config.yaml` is gitignored. `config.example.yaml` is the template. The GUI **Save config** button writes the same file.

```yaml
source: ews
days_back: 7          # midnight UTC, this many days ago
days_forward: 60      # this many days from now
privacy: full         # or busy
ews:
  server: mail.digikala.com
  email: you@company.com
  username: ""        # empty = email; try COMPANY\account if login fails
  auth: ntlm          # or basic
  calendar: ""
  verify_ssl: false   # true only if the server has a public CA certificate
google_calendar: "Work (Outlook)"
```

On Linux/Windows keep `source: ews`. On macOS you may use `source: apple` to read Calendar.app instead.

## Commands

CLI and GUI share `syncer.api` (`get_events`, `run_sync`, …).

| Command | Purpose |
|---|---|
| `python -m syncer gui` | CustomTkinter desktop app |
| `python -m syncer` | Numbered interactive menu |
| `python -m syncer setup` | Google Cloud + config wizard |
| `python -m syncer login-to-outlook` | Save / update Exchange password in the OS keyring |
| `python -m syncer reauth-google` | Delete `token.json` and sign in to Google again |
| `python -m syncer check-outlook-auth` | Test Outlook / Exchange login |
| `python -m syncer show-outlook-events` | List Outlook events in the date window |
| `python -m syncer store` | Fetch Outlook events into encrypted `events.enc` |
| `python -m syncer list-calendars` | List Exchange (or Apple on macOS) calendars |
| `python -m syncer check-google-auth` | Test Google OAuth / token |
| `python -m syncer sync` | Copy events (live from Outlook) |
| `python -m syncer sync --dry-run` | Preview without writing to Google |
| `python -m syncer sync-stored` | Sync Google from a previously encrypted file |
| `python -m syncer sync-stored --dry-run` | Preview sync from the encrypted file |
| `python -m syncer install-schedule --every 15m` | Schedule sync (`15m`/`30m`/`1h`/`3h`/`6h`/`12h`) |
| `python -m syncer uninstall-schedule` | Remove the background schedule |
| `python -m syncer sync-scheduled` | Background sync (macOS notifies on failure) |
| `python -m syncer reset` | Delete Google sync calendar + wipe Outlook/Google credentials (asks `DELETE`) |

### Background schedule by OS

| OS | Mechanism |
|---|---|
| macOS | `launchd` LaunchAgent; failed runs show a Notification Center alert |
| Windows | Task Scheduler + generated `run-sync-scheduled.cmd` |
| Linux | `systemd --user` timer (or cron if systemd is unavailable) |

Pick the interval with `--every` or the GUI dropdown (`15m` … `12h`). Scheduled jobs call `sync-scheduled` so a failed Outlook/Google sync can notify on macOS.

## Platform notes

- **Password storage**: macOS Keychain / Windows Credential Manager / Linux Secret Service (`SecretStorage`). Or set `EWS_PASSWORD`.
- **Linux keyring**: needs a desktop session with a Secret Service (e.g. GNOME Keyring). Headless: use `EWS_PASSWORD`.
- **Windows timezone**: `tzdata` is installed via `requirements.txt` so IANA zones work with `zoneinfo`.
- **pyobjc** (Apple Calendar / Foundation TZ) installs only on macOS.

## If Google says SSL / `UNEXPECTED_EOF` / cannot reach oauth2.googleapis.com

Exchange (VPN) works but **Google is blocked**.

1. Disconnect the VPN briefly.  
2. Run `python -m syncer reauth-google` or GUI **Reauth Google**.  
3. Reconnect VPN, then **Get** / **Sync**.  
4. Better: ask IT for **split tunneling**.

## If Google says `invalid_grant` / token expired

```bash
python -m syncer check-google-auth
python -m syncer reauth-google
python -m syncer sync
```

## If Exchange login fails

1. Confirm the VPN is up and the OWA host opens in a browser.  
2. Try `username` as the full email, then as `DOMAIN\account`.  
3. Try `auth: basic`.  
4. Set `verify_ssl: false` for a corporate TLS certificate.  
5. Re-save the password: `python -m syncer login-to-outlook` or GUI **Login to Outlook**.

## What it will and will not do

| Does | Does not |
|---|---|
| Copy title, time, location, notes (or only “Busy”) | Two-way sync |
| Update Google when Outlook times change | Copy attendees / send invites |
| Delete Google copies that leave the date window | Reach a VPN-only server from the cloud |
| Touch only events it created on the target Google calendar | Replace your personal primary calendar |

## Privacy

- `credentials.json` and `token.json` stay on this machine (gitignored).  
- Exchange password is stored in the **OS keyring**, not in the repo.  
- Prefer `privacy: busy` on a personal Google account.

## Versioning & releases

- Current version: see [`VERSION`](VERSION) (also `python -m syncer --version`).
- Changelog: [`CHANGELOG.md`](CHANGELOG.md) — each GitHub Release should match a section and tag `vX.Y.Z` (example: `v0.8.0`).
- On a Mac, after bumping `VERSION` + `CHANGELOG.md` and committing:

```bash
brew install gh   # once
gh auth login     # once
./scripts/release_macos.sh
```

That script asks whether to release the current `VERSION` or an existing previous tag, can pick from the 5 latest tags, builds release notes from `CHANGELOG.md` between a since-tag and the release version, tags if needed, runs `./scripts/build_macos_dmg.sh`, pushes, and creates the GitHub Release with the DMG attached. Options: `--draft`, `--skip-build`, `--dry-run`, `--tag vX.Y.Z`, `--since vX.Y.Z`.

## License

MIT. See [LICENSE](LICENSE).
