# راهنمای نصب اولیه (macOS)

این راهنما قدم‌به‌قدم برای کسانی است که اولین بار می‌خواهند همگام‌سازی Outlook/Exchange → Google Calendar را روی **مک** راه بیندازند.

اگر انگلیسی راحت‌ترید: [First-time guide (English)](FIRST_TIME_EN.md)

> **نکته اینترنت و VPN (ایران)**
>
> دو حالت جدا دارید — قاطی‌شان نکنید:
>
> 1. **اینترنت با VPN شخصی** برای این کارها لازم است (اینترنت عادی ایران اغلب کافی نیست):
>    - نصب Homebrew و Python
>    - `git clone` و `pip install`
>    - باز کردن Google Cloud Console، دانلود `credentials.json`، و ورود به Gmail
> 2. **دسترسی به ایمیل شرکتی** (مثلاً `mail.digikala.com`):
>    - VPN شخصی را **خاموش** کنید
>    - VPN شرکت را **روشن** کنید، یا به وای‌فایی وصل شوید که ایمیل شرکت روی آن باز می‌شود
>
> اگر VPN شرکت گوگل/Homebrew را می‌بندد، برای آن مراحل دوباره VPN شخصی را روشن کنید (یا از split tunnel استفاده کنید اگر دارید).

---

## ۱. آماده‌سازی Terminal و Homebrew

برنامهٔ **Terminal** را باز کنید. برای نصب Homebrew و Python، **VPN شخصی** را روشن کنید (اینترنت بدون VPN در ایران ممکن است کار نکند).

اگر Homebrew ندارید:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

بعد از نصب موفق، روی مک‌های Apple Silicon معمولاً باید brew را به PATH اضافه کنید (دستورهایی که خود نصب‌کننده چاپ می‌کند را بزنید). نمونه:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

سپس Python 3.11 را نصب کنید:

```bash
HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 brew install python@3.11
```

---

## ۲. ساخت پوشه و دریافت پروژه

مثلاً روی Desktop:

```bash
mkdir -p ~/Desktop/outlook-to-gmail
cd ~/Desktop/outlook-to-gmail
```

کلون از GitHub:

```bash
git clone https://github.com/hamidhandid/outlook-to-gmail-calendar-syncer.git
cd outlook-to-gmail-calendar-syncer
```

---

## ۳. محیط مجازی و نصب وابستگی‌ها

هنوز **VPN شخصی** روشن باشد تا `pip` بتواند پکیج‌ها را دانلود کند.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

صبر کنید تا نصب تمام شود. از این به بعد، هر بار قبل از کار با اسکریپت همان `source .venv/bin/activate` را در همین پوشه بزنید.

---

## ۴. ویزارد اولیه (`setup`)

مراحل Google Cloud و Gmail را با **VPN شخصی** (اینترنت باز به گوگل) انجام دهید.

```bash
python -m syncer setup
```

خروجی تقریبی:

```text
Outlook → Google Calendar setup wizard
======================================

This walks you through creating a personal Google Cloud project,
turning on the Calendar API, and downloading an OAuth client.
It then writes config.yaml for your Exchange server.

Press Enter to start…
```

کلید **Enter** را بزنید و مراحل زیر را در مرورگر دنبال کنید. بعد از هر مرحله به Terminal برگردید و دوباره **Enter** بزنید.

### Step 1 — ساخت پروژه Google Cloud

صفحهٔ New Project باز می‌شود. نامی مثل `outlook-calendar-sync` بگذارید → **Create**. از project picker بالای صفحه همان پروژه را انتخاب کنید.

آدرس:

`https://console.cloud.google.com/projectcreate`

### Step 2 — فعال‌کردن Google Calendar API

مطمئن شوید نام پروژه درست است → **Enable**.

`https://console.cloud.google.com/apis/library/calendar-json.googleapis.com`

### Step 3 — OAuth consent (Google Auth Platform)

1. اگر **Get started** دیدید، بزنید.
2. **App name:** مثلاً `Outlook Calendar Sync`
3. **User support email:** Gmail خودتان
4. **Audience:** گزینهٔ **External** (برای Gmail شخصی؛ Internal فقط برای Google Workspace شرکتی است)
5. **Contact email:** دوباره Gmail خودتان
6. تیک سیاست داده را بزنید و **Create / Finish**

`https://console.cloud.google.com/auth/overview`

### Step 4 — اضافه کردن خودتان به‌عنوان Test user

تا وقتی اپ در حالت Testing است فقط کاربران لیست‌شده می‌توانند وارد شوند.

در صفحهٔ Audience → **Test users** → **Add users** → آدرس کامل Gmail → **Save**.

`https://console.cloud.google.com/auth/audience`

### Step 5 — ساخت Desktop OAuth client (مهم)

1. **Create client**
2. **Application type:** حتماً **Desktop app** (نه Web و نه iOS)
3. **Name:** مثلاً `Mac syncer`
4. **Create**
5. در پنجرهٔ بازشده **Download JSON** را بزنید

`https://console.cloud.google.com/auth/clients`

### Step 6 — ذخیرهٔ `credentials.json`

Terminal مسیر پروژه را نشان می‌دهد، مثلاً:

```text
The file must end up at:
  /Users/YOU/Desktop/outlook-to-gmail/outlook-to-gmail-calendar-syncer/credentials.json
```

اگر فایلی شبیه `client_secret_….apps.googleusercontent.com.json` در Downloads پیدا کند، می‌پرسد کپی شود یا نه:

```text
Copy that file here as credentials.json? [Y/n]:
```

حرف **`Y`** را بزنید و Enter.

---

## ۵. تنظیم اتصال Exchange / Outlook

تقریباً این متن را می‌بینید:

```text
Exchange / Outlook connection
This computer talks to your mail server over Exchange Web Services.
Apple Mail is not required. Connect the company VPN first.
Work email address:
```

| سؤال | پیشنهاد برای Digikala / Fidibo |
|---|---|
| Work email address | ایمیل کاری، مثلاً `you@digikala.com` یا `you@fidibo.com` (نه `@mail.…`) |
| Exchange host | `mail.digikala.com` |
| Username | خالی بگذارید (Enter) مگر لاگین شکست بخورد؛ بعداً می‌توانید `DOMAIN\account` امتحان کنید |
| Auth type | Enter برای پیش‌فرض `ntlm` |
| Verify TLS certificates? | اگر گواهی داخلی شرکت دارید: **`n`** سپس Enter |
| full یا busy | `full` برای جزئیات کامل ایونت؛ Enter یا `busy` فقط برای بلوک Busy |
| Name of the Google calendar | Enter برای پیش‌فرض `Work (Outlook)` |
| Days of past events | عدد روزهای گذشته، یا Enter برای `7` |
| Days of future events | عدد روزهای آینده، یا Enter برای `60` |

سپس:

```text
Save the Exchange password in the system keyring now? [Y/n]:
```

**`Y`** و Enter.

اکنون برای ذخیرهٔ رمز و تست Exchange:

1. VPN شخصی را **خاموش** کنید  
2. VPN شرکت را **روشن** کنید، یا به وای‌فای شرکت / شبکه‌ای وصل شوید که ایمیل کاری روی آن باز است  

```text
Password for you@company.com:
```

رمز را تایپ کنید. در Terminal معمولاً چیزی دیده نمی‌شود؛ بعد از تایپ، Enter بزنید.

```text
Open the Google sign-in now to test Calendar access? [Y/n]:
```

**`Y`** و Enter. برای این مرحله دوباره به اینترنت با **VPN شخصی** نیاز دارید تا Gmail باز شود. در مرورگر Gmail شخصی را انتخاب کنید → **Continue**. بعد از موفقیت:

```text
Setup finished.
```

---

## ۶. استفادهٔ روزمره

برای **خواندن Outlook / sync** معمولاً VPN شرکت (یا وای‌فای شرکت) لازم است؛ برای مشکلات Gmail/توکن دوباره VPN شخصی. هر بار:

```bash
cd ~/Desktop/outlook-to-gmail/outlook-to-gmail-calendar-syncer
source .venv/bin/activate
python -m syncer
```

منوی شماره‌دار باز می‌شود. مهم‌ترین گزینه‌ها:

| شماره | کار |
|---|---|
| **9** | `get` — لیست ایونت‌های Outlook در بازهٔ تاریخ (پیش‌فرض حدود ۷ روز قبل تا ۶۰ روز بعد) |
| **10** | `sync --dry-run` — پیش‌نمایش بدون نوشتن در Google |
| **11** | `sync` — کپی ایونت‌ها به Google Calendar |
| **1** | `gui` — اپ گرافیکی (در صورت نصب Tk) |

اگر گزینهٔ ۹ ایونت‌ها را نشان داد، سمت Exchange معمولاً درست است. بعد گزینهٔ ۱۱ را برای نوشتن در Google بزنید.

موفق باشید.
