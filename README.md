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

The **setup wizard** opens the Google Cloud pages in your browser and pauses after each step so you can:

1. Create a Google Cloud project
2. Enable the **Google Calendar API**
3. Configure the OAuth consent screen (External + yourself as a test user)
4. Create a **Desktop** OAuth client and save `credentials.json`
5. Write `config.yaml` for your Exchange host
6. Optionally store the Exchange password in Keychain and test Google login

Google-only (if `config.yaml` is already filled in):

```bash
python -m syncer setup --google-only
```

Then, with the VPN connected:

```bash
python -m syncer login          # Exchange password → Keychain
python -m syncer check
python -m syncer sync --dry-run
python -m syncer sync
python -m syncer install-schedule   # optional, every 15 minutes
```

Events appear in Google Calendar under the calendar name you chose (default **Work (Outlook)**).

## What `setup` will ask you to click in Google Cloud

Sign in with the **Gmail that should receive the work calendar**. Keep the **project picker** at the top of the console on the project you create.

| Step | What to do |
|---|---|
| New project | Name it `outlook-calendar-sync` → Create |
| Calendar API | [Enable this API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com) |
| Auth platform | Get started → app name → **External** audience → your Gmail as contact |
| Test user | **Audience → Add users** → your Gmail |
| OAuth client | **Create client → Desktop app** → Download JSON → save as `credentials.json` in this folder |

If Google says the app is unverified, choose **Advanced → Go to … (unsafe)**. That is expected for a personal project. Do not publish or request Google verification.

While the app stays in **Testing**, Google may expire the login after **7 days**. Run `python -m syncer check` again to re-authorize.

## Config

`config.yaml` is gitignored. `config.example.yaml` is the template.

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

`source: apple` is only if the work account is already in **System Settings → Internet Accounts**.

## Commands

| Command | Purpose |
|---|---|
| `python -m syncer setup` | Interactive Google Cloud + config wizard |
| `python -m syncer login` | Save Exchange password in Keychain |
| `python -m syncer list-calendars` | List Exchange (or Apple) calendars |
| `python -m syncer check` | Test Exchange + Google login |
| `python -m syncer sync` | Copy events |
| `python -m syncer install-schedule` | launchd, every 15 minutes |
| `python -m syncer uninstall-schedule` | Remove launchd job |

## If Exchange login fails

1. Confirm the VPN is up and the OWA host opens in a browser.
2. Try `username` as the full email, then as `DOMAIN\account`.
3. Try `auth: basic`.
4. Set `verify_ssl: false` for a corporate TLS certificate.
5. If IT disabled EWS or requires MFA that a password cannot satisfy, this tool cannot sign in.

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

## License

MIT. See [LICENSE](LICENSE).
