# First-time setup guide (macOS) — desktop app

فارسی: [راهنمای نصب اولیه](FIRST_TIME_FA.md)

This guide is for installing from the **DMG** and using the **graphical app** (no Terminal required).  
If you prefer installing from the **Terminal**, see the **optional** Terminal guide at the end.

---

## Internet and VPN (important)

In Iran these two networks get mixed up often. Simple rule:

| Task | Network you need |
|---|---|
| Installing the app, reaching **Gmail / Google Cloud**, cloning from GitHub | A **personal VPN** that bypasses sanctions |
| Logging into **company email / Outlook / Exchange**, listing work events | **Company VPN** or company Wi‑Fi (turn the personal VPN **off**) |

You usually cannot use one VPN for both. Switch between them.

---

## 1) Install from the DMG

1. Get the latest build from the GitHub Releases page:  
   [Latest release](https://github.com/hamidhandid/outlook-to-gmail-calendar-syncer/releases/latest)  
   Download the **`.dmg`** file (e.g. `Outlook-to-Google-Calendar-Syncer-….dmg`) and open it.
2. Drag **Outlook to Google Calendar Syncer** into **Applications**.
3. Open the app from Applications (double-click).

### First launch blocked by macOS?

If the app is not yet signed/notarized with an Apple Developer ID, macOS may refuse to open it.

1. Go to **System Settings → Privacy & Security**.
2. Near the bottom you should see a message like “Outlook to Google Calendar Syncer was blocked…”.
3. Click **Open Anyway** and confirm.

Then open the app from Applications again.

### Mac password and Always Allow

Whenever the app starts (or when it saves your Outlook password), macOS may ask for **Keychain** access and your Mac login password.

- Enter your Mac password.
- If you see **Always Allow**, choose that so it does not ask every time.

App data lives here:

`~/Library/Application Support/outlook-to-gmail-calendar-syncer/`

(**Open data folder** in the app opens the same path.)

---

## 2) Quick tour of the window

**Left — config and Outlook**

- `days_back` / `days_forward` — how many days of past/future events (defaults 7 and 60)
- `email` — work email
- **Login to Outlook** / **Check Outlook auth**
- `server` — default `mail.digikala.com`
- `username` — leave empty (same as email) unless IT says otherwise
- `auth` — usually `ntlm`
- **verify SSL** — usually leave **unchecked**
- **Save config** — writes settings

**Right — Google**

- Google calendar name (default `Work (Outlook)`)
- **Setup Google** — wizard to create the Cloud project and `credentials.json`
- **Sign in to Google** / **Reauth Google** / **Check Google auth**
- `privacy` — default `full` (titles and details). Use `busy` for Busy-only blocks

**Bottom**

- **Show events from outlook** — list Exchange events
- **Sync** — copy those events to Google (enabled after a successful Get)
- **Sync dry-run** — preview only, no Google writes
- **Every** + **Install schedule** — automatic runs (for example every 30 minutes)

---

## 3) First: log in to Outlook

For this section turn the **company VPN on** and the personal VPN **off**.

1. In **email**, type your work address, e.g. `you@digikala.com` or `you@fidibo.com`  
   (not `@mail.digikala.com` — that is the server host, not your mailbox).
2. Confirm **server** is correct (often `mail.digikala.com`).
3. Click **Save config**.
4. Click **Login to Outlook** and enter your work email password.
5. If macOS asks about Keychain: Mac password + **Always Allow** if offered.
6. Click **Check Outlook auth** to confirm success.

If login fails:

- Are you still on company VPN / Wi‑Fi?
- Leave `username` empty; if needed try `COMPANY\account`.
- Switch `auth` between `ntlm` and `basic`, then Save + Login again.

---

## 4) Next: Setup Google (screenshot for each step)

For this section turn your **personal (anti-sanctions) VPN on**.

Click **Setup Google**. The app opens the browser step by step and shows a guide screenshot for each action. After you finish the browser work, click **Confirm** in the app to continue. If you quit midway, click **Setup Google** again — it resumes where you left off.

Screenshots use `example@gmail.com`; use your real Gmail.

### Step 1 — Create a Google Cloud project

Pick a project name (e.g. `outlook-calendar-sync`) and click **Create**. At the top of the page, make sure that project is selected.

![Step 1 — Create a Google Cloud project](assets/google-setup/step-01.png)

### Step 2 — Enable the Google Calendar API

Click **Enable**. When it finishes, return to the app and Confirm.

![Step 2 — Enable Calendar API](assets/google-setup/step-02.png)

### Step 3 — OAuth / Google Auth Platform

#### 3‑1) Get started

If you see “Google Auth Platform not configured yet”, click **Get started**.

![Step 3 — Get started](assets/google-setup/step-03.png)

#### 3‑2) App name and User support email

1. App name e.g. `Outlook Calendar Sync`
2. User support email: your Gmail
3. **Next**

![Step 3 — App name & support email](assets/google-setup/step-04.png)

#### 3‑3) Audience = External

For a personal Gmail choose **External** (Internal is only for company Workspace), then **Next**.

![Step 3 — Audience External](assets/google-setup/step-05.png)

#### 3‑4) Contact Information

Enter your email again and click **Next**.

![Step 3 — Contact Information](assets/google-setup/step-06.png)

#### 3‑5) Finish

Check **I agree…**, click **Continue** if shown, then **Create**.

![Step 3 — Finish / Create](assets/google-setup/step-07.png)

### Step 4 — Add yourself as a test user

Click **+ Add users**:

![Step 4 — Add users](assets/google-setup/step-08.png)

Type your full Gmail, press Enter (so it becomes a chip), then **Save**:

![Step 4 — Type Gmail and Save](assets/google-setup/step-09.png)

### Step 5 — Create a Desktop client and download JSON

1) Click **Create client**:

![Step 5 — Create client](assets/google-setup/step-10.png)

2) Application type: **Desktop app** (not Web, not iOS). Name e.g. `Mac syncer`, then **Create**:

![Step 5 — Desktop app + name](assets/google-setup/step-11.png)

3) In the popup click **Download JSON**:

![Step 5 — Download JSON](assets/google-setup/step-12.png)

### Step 6 — Save as credentials.json

The downloaded file must end up in the app data folder as **`credentials.json`**. The wizard usually offers to copy it from Downloads — Confirm. Or use **Import credentials** and pick that JSON.

![Step 6 — Save credentials.json](assets/google-setup/step-13.png)

### Sign in to Gmail (token.json)

After Setup, if you see **Sign in to Google**, click it (personal VPN still on). In the browser pick your Gmail and Continue.

If Google says the app is unverified: **Advanced → Go to … (unsafe)** — normal for personal use.

While the Cloud app stays in **Testing**, Google may expire the login after about **7 days** — click **Reauth Google** when that happens.

Use **Check Google auth** to verify everything is ready.

---

## 5) Fetch events and sync

Once **both Outlook and Google** are set up:

### Show Outlook events

1. Turn the **company VPN** on.
2. Click **Show events from outlook**.
3. Events should appear in the Outlook events pane. If not, re-check Outlook login and company VPN.

### Copy to Google Calendar

1. If the company network blocks Google, turn the **personal VPN** on.
2. Click **Sync** (enabled after a successful Show events).
3. Events appear under the Google calendar name you chose (default **Work (Outlook)**). The app also sets a default **15-minute** popup reminder on that calendar.

Use **Sync dry-run** first if you only want a preview.

### Company mail now, Google later

1. On company VPN: **Get from outlook and Store encrypted** — asks for a separate password for the encrypted file.
2. Later, when Google is reachable: **Sync from encrypted file** — same password, no second Outlook fetch.

---

## 6) Automatic sync (e.g. every 30 minutes)

To have the Mac repeat this for you:

1. In the Schedule row, set **Every** to **`30m`** (or `15m` / `1h` / `3h` / `6h` / `12h`).
2. Click **Install schedule**.
3. macOS uses **launchd**. If a background run fails, you may get a Notification Center alert.

To stop: **Uninstall schedule**.

Note: for automatic sync to succeed, at run time your Mac still needs to reach the company mail server (company VPN/Wi‑Fi) and, when required, Google — depending on your network.

---

## Quick checklist

- [ ] DMG installed; **Open Anyway** in Privacy & Security if needed  
- [ ] Keychain prompt: Mac password + **Always Allow** when offered  
- [ ] On company VPN: **Login to Outlook** succeeded  
- [ ] On personal VPN: **Setup Google** + **Sign in to Google** succeeded  
- [ ] **Show events from outlook** listed events  
- [ ] **Sync** copied them to Google  
- [ ] Optional: **Every → 30m → Install schedule**

Good luck!

---

## Optional — Terminal-based install and setup

> This section is **optional** and only for people who want to use the **Terminal** (Homebrew, git clone, `python -m syncer setup`). Most users only need the **DMG + desktop app** guide above.

Before we start — one important thing about internet and VPN (this trips people up a lot in Iran):

- Whenever you need **Gmail**, or to install **Homebrew / brew**, or to install Python packages (`pip install`) and download the project from GitHub, turn on a **personal VPN**. Plain Iranian internet often is **not** enough and things will hang or fail.
- Whenever you need **company email** (for example the server `mail.digikala.com`), turn your **personal VPN off** and turn the **company VPN on**. Or join Wi‑Fi where company mail actually opens.

OK — let’s do it.

---

First, if you have a good personal VPN, turn it on (you’ll need it for installs and Google).

Then open the **Terminal** app.

If you don’t have **Homebrew / brew** on your Mac yet, paste this into Terminal and press Enter:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Wait until it finishes. If at the end it prints a few lines telling you to add something to `~/.zprofile`, copy those commands and run them. On newer Macs a common version looks like this:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

After brew installed successfully, run this so Python 3.11 gets installed:

```bash
HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 brew install python@3.11
```

Now make a folder. For example, to create a folder named `outlook-to-gmail` on your Desktop:

```bash
mkdir -p ~/Desktop/outlook-to-gmail
```

Go into that folder:

```bash
cd ~/Desktop/outlook-to-gmail
```

Now run this to download the project from GitHub (keep the personal VPN on):

```bash
git clone https://github.com/hamidhandid/outlook-to-gmail-calendar-syncer.git
```

Then go into the folder that was just downloaded:

```bash
cd outlook-to-gmail-calendar-syncer
```

Now this:

```bash
python3.11 -m venv .venv
```

Then this:

```bash
source .venv/bin/activate
```

Then run this and wait until it fully finishes (personal VPN still on):

```bash
pip install -r requirements.txt
```

When that’s done, run this to start the first-time setup for your Google calendar (personal VPN still on — we’re talking to Google):

```bash
python -m syncer setup
```

You’ll see something like:

```text
Outlook → Google Calendar setup wizard
======================================

This walks you through creating a personal Google Cloud project,
turning on the Calendar API, and downloading an OAuth client.
It then writes config.yaml for your Exchange server.

Press Enter to start…
```

Press **Enter** on your keyboard.

Then you’ll see Step 1 (Create a Google Cloud project) and a browser page should open. Pick a project name (for example `outlook-calendar-sync`) and click Create. At the top of the page, make sure that same project is selected.

Come back to Terminal and press **Enter** again.

Now you’ll see Step 2 (Enable the Google Calendar API). In the browser click **Enable**. When it’s done, go back to Terminal and press Enter.

Then Step 3 (OAuth consent / Google Auth Platform). In the GUI each click has its own screenshot; in the browser:

1. If you see **Get started**, click it.
2. For App name, type something like `Outlook Calendar Sync`.
3. For User support email, pick your Gmail and click Next.
4. Set Audience to **External** and click Next. (Internal is only for a company Google Workspace account. Personal Gmail must be External.)
5. For Contact Information put your email again and click Next.
6. Check the box at the end and click Continue / Create.

Come back to Terminal and press Enter.

Step 4 — Add yourself as a test user. In the browser, under Test users click **Add users**, type your full Gmail, Save. Back to Terminal → Enter.

Now Step 5 — this one is important:

In the browser click **Create client**. For Application type choose **Desktop app** (not Web, not iOS). Give it a name like `Mac syncer` and click Create. In the popup click **Download JSON**.

Back to Terminal → Enter.

You’ll see something like this (paths will be different on your Mac):

```text
Step 6 — Save credentials.json in this project
The file must end up at:
  /Users/YOU/Desktop/outlook-to-gmail/outlook-to-gmail-calendar-syncer/credentials.json
Found a Google client file in Downloads:
  /Users/YOU/Downloads/client_secret_….apps.googleusercontent.com.json
Copy that file here as credentials.json? [Y/n]:
```

Here type **`Y`** and press Enter.

Now you’ll see:

```text
Exchange / Outlook connection
This computer talks to your mail server over Exchange Web Services.
Apple Mail is not required. Connect the company VPN first.
Work email address:
```

Type your work email here. For example `you@digikala.com` or `you@fidibo.com` (don’t type `@mail.digikala.com` — that’s the server name, not your email). Press Enter.

Next it asks:

```text
Exchange host (from OWA, without https://) [mail.digikala.com]:
```

The default is already `mail.digikala.com` — you can just press Enter. For username you can leave it empty and just press Enter.

If you see:

```text
Auth type: ntlm or basic [ntlm]:
```

just press Enter again (leave it on ntlm).

Then:

```text
Verify TLS certificates? Choose n if the company uses an internal CA [y/N]:
```

Default is **`n`** — usually just press Enter (unless the server has a public CA cert).

Then:

```text
Copy full details (full) or only Busy blocks (busy)? [full]:
```

Default is **`full`** (titles and details). Type `busy` and Enter if you only want Busy blocks.

Then:

```text
Name of the Google calendar to create/use [Work (Outlook)]:
```

You can just press Enter.

Then:

```text
Days of past events to copy [7]:
```

This tells the script how many days back to copy. Type a number, or press Enter for the default of 7.

Then:

```text
Days of future events to copy [60]:
```

Same idea for the future — Enter means 60 days ahead, or type your own number.

Then you’ll see:

```text
Save the Exchange password in the system keyring now? [Y/n]:
```

Type **`Y`** and press Enter.

Important: so it can reach company email, turn your **personal VPN off** and turn the **company VPN on** (or join Wi‑Fi where company mail opens).

You’ll see:

```text
Password for you@company.com:
```

Type your email password. Don’t worry if Terminal doesn’t show any characters — that’s normal. Type it anyway, then press Enter.

Then:

```text
Open the Google sign-in now to test Calendar access? [Y/n]:
```

Type **`Y`** and press Enter. For this step turn the **personal VPN back on** so Gmail can open. In the browser pick your Gmail account and click Continue. You can close that tab afterward. When you go back to Terminal you should basically see:

```text
Setup finished.
```

---

From now on, whenever you want to use it, open Terminal and go to that same folder. In this example it was:

`~/Desktop/outlook-to-gmail/outlook-to-gmail-calendar-syncer`

So:

```bash
cd ~/Desktop/outlook-to-gmail/outlook-to-gmail-calendar-syncer
```

Then:

```bash
source .venv/bin/activate
```

Then:

```bash
python -m syncer
```

You’ll get a numbered menu. For example, number **9** shows your events (by default from about 7 days ago to 60 days ahead). If you see your events, Outlook/Exchange is probably fine — just remember you need company VPN / company Wi‑Fi for that.

Then run `python -m syncer` again and pick **11** to copy those Outlook events into your Google Calendar. If Google acts up in the middle, you may need the personal VPN again.

If you can reach company mail now but want to sync to Google later: use **14** (`store`) to save events into a password-encrypted file, then later use **16** (`sync-stored`) to push that file to Google Calendar (no second Outlook fetch).

Good luck!
