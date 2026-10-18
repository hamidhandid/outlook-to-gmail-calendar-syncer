# First-time setup guide (macOS)

فارسی: [راهنمای نصب اولیه](FIRST_TIME_FA.md)

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
