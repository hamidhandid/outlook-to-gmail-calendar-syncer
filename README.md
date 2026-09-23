# outlook-to-gmail-calendar-syncer

One-way copy of an **Outlook / Exchange** calendar into a **dedicated Google calendar**. Your Mac is the bridge: it reads Exchange (often only reachable on a company VPN) and writes copies to Google.

Apple Mail is not required. Attendees are not copied, so coworkers do not get extra invites.

This is a **personal** tool. Check with IT before copying a work calendar to a personal Google account.

## Quick start

Python 3.11+ (Homebrew `python3.13` is fine; the system `/usr/bin/python3` on macOS is often 3.9 and will not work well).

```bash
git clone https://github.com/hamidhandid/outlook-to-gmail-calendar-syncer.git
cd outlook-to-gmail-calendar-syncer
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m syncer setup
```

### GUI (recommended for ordinary users)

```bash
# Homebrew Python needs the Tk package once:
brew install python-tk@3.13

pip install -r requirements.txt   # includes customtkinter
python -m syncer gui
```

The desktop app follows the **system light/dark** theme and uses the same core as the CLI:

1. Fill **days_back**, **days_forward**, email, server, privacy, etc. → **Save config** (writes `config.yaml`)
2. **Login Exchange** / **Reauth Google** / **Check tokens** as needed
3. **Get** — loads Outlook events into the list (VPN on)
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
python -m syncer login
python -m syncer tokens
python -m syncer get              # list events in the date window
python -m syncer sync --dry-run
python -m syncer sync
python -m syncer install-schedule # optional, every 15 minutes
```

Events appear in Google Calendar under the name you chose (default **Work (Outlook)**).

## Config

`config.yaml` is gitignored. `config.example.yaml` is the template. The GUI **Save config** button writes the same file.

```yaml
source: ews
days_back: 7          # midnight UTC, this many days ago
days_forward: 60      # this many days from now
privacy: busy         # or full
ews:
  server: mail.company.com
  email: you@company.com
  username: ""        # empty = email; try COMPANY\account if login fails
  auth: ntlm          # or basic
  calendar: ""
  verify_ssl: true    # false if the server uses an internal certificate
google_calendar: "Work (Outlook)"
```

## Commands

CLI and GUI share `syncer.api` (`get_events`, `run_sync`, …).

| Command | Purpose |
|---|---|
| `python -m syncer gui` | CustomTkinter desktop app |
| `python -m syncer` | Numbered interactive menu |
| `python -m syncer setup` | Google Cloud + config wizard |
| `python -m syncer login` | Save / update Exchange password in Keychain |
| `python -m syncer reauth-google` | Delete `token.json` and sign in to Google again |
| `python -m syncer tokens` | Check Exchange + Google token / login status |
| `python -m syncer get` | List Outlook events in the date window |
| `python -m syncer list-calendars` | List Exchange (or Apple) calendars |
| `python -m syncer check` | Test Exchange + Google login |
| `python -m syncer sync` | Copy events |
| `python -m syncer sync --dry-run` | Preview without writing to Google |
| `python -m syncer install-schedule` | launchd, every 15 minutes |
| `python -m syncer uninstall-schedule` | Remove launchd job |

## If Google says SSL / `UNEXPECTED_EOF` / cannot reach oauth2.googleapis.com

Exchange (VPN) works but **Google is blocked**.

1. Disconnect the VPN briefly.  
2. Run `python -m syncer reauth-google` or GUI **Reauth Google**.  
3. Reconnect VPN, then **Get** / **Sync**.  
4. Better: ask IT for **split tunneling**.

## If Google says `invalid_grant` / token expired

```bash
python -m syncer tokens
python -m syncer reauth-google
python -m syncer sync
```

## If Exchange login fails

1. Confirm the VPN is up and the OWA host opens in a browser.  
2. Try `username` as the full email, then as `DOMAIN\account`.  
3. Try `auth: basic`.  
4. Set `verify_ssl: false` for a corporate TLS certificate.  
5. Re-save the password: `python -m syncer login` or GUI **Login Exchange**.

## What it will and will not do

| Does | Does not |
|---|---|
| Copy title, time, location, notes (or only “Busy”) | Two-way sync |
| Update Google when Outlook times change | Copy attendees / send invites |
| Delete Google copies that leave the date window | Reach a VPN-only server from the cloud |
| Touch only events it created on the target Google calendar | Replace your personal primary calendar |

## Privacy

- `credentials.json` and `token.json` stay on your Mac (gitignored).  
- Exchange password is stored in **macOS Keychain**, not in the repo.  
- Prefer `privacy: busy` on a personal Google account.

## Versioning & releases

- Current version: see [`VERSION`](VERSION) (also `python -m syncer --version`).
- Changelog: [`CHANGELOG.md`](CHANGELOG.md) — each GitHub Release should match a section and tag `vX.Y.Z` (example: `v0.2.0`).
- Tag locally after bumping `VERSION` + changelog, then push the tag and attach build artifacts on GitHub Releases.

## License

MIT. See [LICENSE](LICENSE).
