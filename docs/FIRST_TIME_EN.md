# First-time setup guide (macOS)

Step-by-step for people setting up Outlook/Exchange → Google Calendar sync on a **Mac** for the first time.

فارسی: [راهنمای نصب اولیه](FIRST_TIME_FA.md)

> **VPN tip**
>
> - For **Google Cloud** and Gmail sign-in you usually need normal internet (turn off a company VPN that blocks Google, or use split tunneling).
> - For the **work mailbox** (for example `mail.digikala.com`) the **company VPN** must be on.
> - If a personal VPN breaks access to the company mail server, turn that personal VPN off for the Exchange steps.

Windows / Linux users: use the [README Quick start](../README.md#quick-start); the Google + Exchange wizard (`python -m syncer setup`) is the same idea.

---

## 1. Terminal and Homebrew

Open **Terminal**.

If Homebrew is not installed:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

On Apple Silicon, add brew to your PATH if the installer tells you to, for example:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Install Python 3.11:

```bash
HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 brew install python@3.11
```

---

## 2. Folder and clone

```bash
mkdir -p ~/Desktop/outlook-to-gmail
cd ~/Desktop/outlook-to-gmail
git clone https://github.com/hamidhandid/outlook-to-gmail-calendar-syncer.git
cd outlook-to-gmail-calendar-syncer
```

---

## 3. Virtualenv and dependencies

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Wait until pip finishes. Later sessions: activate `.venv` again from this project folder before running commands.

---

## 4. Setup wizard

```bash
python -m syncer setup
```

You should see:

```text
Outlook → Google Calendar setup wizard
======================================

This walks you through creating a personal Google Cloud project,
turning on the Calendar API, and downloading an OAuth client.
It then writes config.yaml for your Exchange server.

Press Enter to start…
```

Press **Enter**, follow each browser step, then return to Terminal and press **Enter** again.

### Step 1 — Create a Google Cloud project

Name it something like `outlook-calendar-sync` → **Create**. Select that project in the top project picker.

`https://console.cloud.google.com/projectcreate`

### Step 2 — Enable the Google Calendar API

Confirm the project name → **Enable**.

`https://console.cloud.google.com/apis/library/calendar-json.googleapis.com`

### Step 3 — OAuth consent (Google Auth Platform)

1. Click **Get started** if shown.
2. **App name:** e.g. `Outlook Calendar Sync`
3. **User support email:** your Gmail
4. **Audience:** **External** (required for personal Gmail; Internal is Workspace-only)
5. **Contact email:** your Gmail again
6. Accept the policy → **Create / Finish**

`https://console.cloud.google.com/auth/overview`

### Step 4 — Add yourself as a test user

While the app is in Testing, only listed accounts can sign in.

Audience → **Test users** → **Add users** → your full Gmail → **Save**.

`https://console.cloud.google.com/auth/audience`

### Step 5 — Create a Desktop OAuth client (important)

1. **Create client**
2. **Application type:** **Desktop app** (not Web, not iOS)
3. **Name:** e.g. `Mac syncer`
4. **Create**
5. **Download JSON**

`https://console.cloud.google.com/auth/clients`

### Step 6 — Save `credentials.json`

The wizard prints the required path, for example:

```text
The file must end up at:
  /Users/YOU/Desktop/outlook-to-gmail/outlook-to-gmail-calendar-syncer/credentials.json
```

If it finds a `client_secret_….apps.googleusercontent.com.json` in Downloads:

```text
Copy that file here as credentials.json? [Y/n]:
```

Type **`Y`** and Enter.

---

## 5. Exchange / Outlook answers

```text
Exchange / Outlook connection
…
Work email address:
```

| Prompt | Typical Digikala / Fidibo answer |
|---|---|
| Work email address | Work address, e.g. `you@digikala.com` or `you@fidibo.com` (not `@mail.…`) |
| Exchange host | `mail.digikala.com` |
| Username | Leave empty (Enter); if login fails later, try `DOMAIN\account` |
| Auth type | Enter for default `ntlm` |
| Verify TLS certificates? | **`n`** if the company uses an internal CA |
| full or busy | `full` for titles/notes; Enter / `busy` for Busy blocks only |
| Google calendar name | Enter for `Work (Outlook)` |
| Days past / future | Numbers, or Enter for `7` / `60` |

Then:

```text
Save the Exchange password in the system keyring now? [Y/n]:
```

**`Y`** → Enter. Turn the **company VPN** on for mail access.

```text
Password for you@company.com:
```

Type the password (characters usually stay hidden) → Enter.

```text
Open the Google sign-in now to test Calendar access? [Y/n]:
```

**`Y`** → Enter. Use normal internet if the company VPN blocks Google. Pick your personal Gmail → **Continue**. When done:

```text
Setup finished.
```

---

## 6. Day-to-day use

```bash
cd ~/Desktop/outlook-to-gmail/outlook-to-gmail-calendar-syncer
source .venv/bin/activate
python -m syncer
```

Useful menu numbers:

| # | Command | Purpose |
|---|---|---|
| **9** | `get` | List Outlook events in the date window (default ~7 days back … 60 ahead) |
| **10** | `sync --dry-run` | Preview without writing to Google |
| **11** | `sync` | Copy events into Google Calendar |
| **1** | `gui` | Desktop app (needs Tk) |

If **9** shows events, Exchange is probably fine. Use **11** to write to Google.

Good luck.
