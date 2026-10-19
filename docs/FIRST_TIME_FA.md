# راهنمای نصب اولیه (macOS) — اپلیکیشن گرافیکی

اگه انگلیسی راحت‌ترید: [First-time guide (English)](FIRST_TIME_EN.md)

این راهنما برای **نصب از فایل DMG** و کار با **پنجرهٔ برنامه** است (بدون Terminal).  
اگه ترجیح می‌دی از **Terminal** نصب کنی، آخر همین فایل بخش **اختیاری** (راهنمای Terminal) را ببین.

---

## اینترنت و وی‌پی‌ان (خیلی مهم)

تو ایران قاطی کردن این دو تا خیلی پیش میاد. قانون ساده:

| کار | چه اینترنتی لازم است |
|---|---|
| نصب برنامه، وصل شدن به **Gmail / Google Cloud**، دانلود از گیت‌هاب | **وی‌پی‌ان شخصی** که تحریم‌ها را دور بزند |
| لاگین به **ایمیل شرکتی / Outlook / Exchange**، دیدن ایونت‌های کاری | **وی‌پی‌ان شرکت** یا وای‌فای شرکت (وی‌پی‌ان شخصی را خاموش کن) |

یادت باشد: برای Outlook و Google معمولاً **هم‌زمان یک وی‌پی‌ان** کافی نیست — بین این دو سوییچ کن.

---

## ۱) نصب از فایل DMG

1. آخرین نسخه را از صفحهٔ Releases گیت‌هاب بگیر:  
   [Latest release](https://github.com/hamidhandid/outlook-to-gmail-calendar-syncer/releases/latest)  
   فایل **`.dmg`** را دانلود کن (مثلاً `Outlook-to-Google-Calendar-Syncer-….dmg`) و باز کن.
2. آیکون **Outlook to Google Calendar Syncer** را بکش داخل پوشهٔ **Applications**.
3. از Applications برنامه را باز کن (دبل‌کلیک).

### اولین بار: macOS اجازه نمی‌دهد؟

چون برنامه ممکن است هنوز با Apple Developer ID امضا/نوتاریز نشده باشد، مک گاهی می‌گوید نمی‌تواند بازش کند.

1. برو به **System Settings → Privacy & Security**.
2. پایین صفحه پیغامی شبیه «Outlook to Google Calendar Syncer was blocked…» می‌بینی.
3. روی **Open Anyway** بزن و تأیید کن.

بعد دوباره برنامه را از Applications باز کن.

### پسورد مک و Always Allow

هر بار که برنامه باز می‌شود (یا وقتی پسورد Outlook را ذخیره می‌کند)، مک ممکن است از **Keychain** بپرسد و پسورد سیستم را بخواهد.

- پسورد لاگین مک خودت را بزن.
- اگر گزینهٔ **Always Allow** دیدی، همان را بزن تا هر بار دوباره نپرسد.

داده‌های برنامه اینجا ذخیره می‌شود:

`~/Library/Application Support/outlook-to-gmail-calendar-syncer/`

(دکمهٔ **Open data folder** داخل برنامه هم همین مسیر را باز می‌کند.)

---

## ۲) نگاه سریع به صفحهٔ برنامه

وقتی برنامه باز شد:

**سمت چپ — تنظیمات و Outlook**

- `days_back` / `days_forward` — چند روز قبل و بعد از امروز ایونت بیاید (پیش‌فرض ۷ و ۶۰)
- `email` — ایمیل کاری
- **Login to Outlook** / **Check Outlook auth**
- `server` — پیش‌فرض `mail.digikala.com`
- `username` — معمولاً خالی بگذار (یعنی همان ایمیل)
- `auth` — معمولاً `ntlm`
- تیک **verify SSL** — معمولاً **خاموش** بماند
- **Save config** — ذخیرهٔ تنظیمات

**سمت راست — Google**

- نام تقویم گوگل (پیش‌فرض `Work (Outlook)`)
- **Setup Google** — جادوگر ساخت پروژه و دانلود `credentials.json`
- **Sign in to Google** / **Reauth Google** / **Check Google auth**
- `privacy` — پیش‌فرض `full` (عنوان و جزئیات). اگر فقط «مشغول» می‌خواهی بگذار `busy`

**پایین صفحه**

- **Show events from outlook** — لیست ایونت‌ها از Exchange
- **Sync** — کپی همان ایونت‌ها به گوگل‌کلندر (بعد از یک Get موفق فعال می‌شود)
- **Sync dry-run** — فقط پیش‌نمایش، بدون نوشتن روی گوگل
- **Every** + **Install schedule** — اجرای خودکار (مثلاً هر ۳۰ دقیقه)

---

## ۳) اول: لاگین به Outlook

برای این بخش وی‌پی‌ان شرکت را **روشن** کن و وی‌پی‌ان شخصی را **خاموش** کن.

1. در فیلد **email** ایمیل کاری‌ات را بنویس، مثلاً `you@digikala.com` یا `you@fidibo.com`  
   (نه `@mail.digikala.com` — آن آدرس سرور است، نه ایمیل تو.)
2. مطمئن شو **server** درست است (برای خیلی‌ها `mail.digikala.com`).
3. روی **Save config** بزن.
4. روی **Login to Outlook** بزن و پسورد ایمیل کاری را وارد کن.
5. اگر مک Keychain را پرسید: پسورد سیستم + در صورت امکان **Always Allow**.
6. برای اطمینان **Check Outlook auth** را بزن؛ باید پیام موفقیت ببینی.

اگر لاگین رد شد:

- هنوز روی وی‌پی‌ان/وای‌فای شرکت هستی؟
- `username` را خالی بگذار؛ اگر باز نشد گاهی فرمت `COMPANY\account` لازم است.
- `auth` را در صورت نیاز بین `ntlm` و `basic` عوض کن و دوباره Save + Login.

---

## ۴) بعد: Setup Google (با اسکرین‌شات هر مرحله)

برای این بخش وی‌پی‌ان شخصی (ضد تحریم) را **روشن** کن.

روی **Setup Google** بزن. برنامه قدم‌به‌قدم مرورگر را باز می‌کند و برای هر مرحله اسکرین‌شات راهنما نشان می‌دهد. بعد از هر کار در مرورگر، در پنجرهٔ برنامه **Confirm** بزن تا برود مرحلهٔ بعد. اگر وسط کار بستی، دوباره **Setup Google** را بزن — از همان جایی که مانده ادامه می‌دهد.

در اسکرین‌شات‌ها ایمیل نمونه `example@gmail.com` است؛ تو جیمیل واقعی خودت را بگذار.

### Step 1 — ساخت پروژه در Google Cloud

اسم پروژه را بگذار (مثلاً `outlook-calendar-sync`) و **Create** را بزن. از بالای صفحه مطمئن شو همان پروژه انتخاب شده.

![Step 1 — Create a Google Cloud project](assets/google-setup/step-01.png)

### Step 2 — روشن کردن Google Calendar API

روی **Enable** بزن. وقتی اوکی شد برگرد به برنامه و Confirm.

![Step 2 — Enable Calendar API](assets/google-setup/step-02.png)

### Step 3 — OAuth / Google Auth Platform

#### ۳‑۱) Get started

اگر دیدی «Google Auth Platform not configured yet»، روی **Get started** بزن.

![Step 3 — Get started](assets/google-setup/step-03.png)

#### ۳‑۲) App name و User support email

1. App name مثلاً `Outlook Calendar Sync`
2. User support email: جیمیل خودت
3. **Next**

![Step 3 — App name & support email](assets/google-setup/step-04.png)

#### ۳‑۳) Audience = External

برای جیمیل شخصی حتماً **External** را انتخاب کن (Internal فقط برای Workspace شرکتی است)، بعد **Next**.

![Step 3 — Audience External](assets/google-setup/step-05.png)

#### ۳‑۴) Contact Information

دوباره ایمیل خودت را بزن و **Next**.

![Step 3 — Contact Information](assets/google-setup/step-06.png)

#### ۳‑۵) Finish

تیک **I agree…** را بزن، در صورت وجود **Continue**، بعد **Create**.

![Step 3 — Finish / Create](assets/google-setup/step-07.png)

### Step 4 — خودت را به عنوان Test user اضافه کن

روی **+ Add users** بزن:

![Step 4 — Add users](assets/google-setup/step-08.png)

جیمیل کامل خودت را بنویس، Enter بزن (تا به صورت chip دربیاید)، بعد **Save**:

![Step 4 — Type Gmail and Save](assets/google-setup/step-09.png)

### Step 5 — ساخت Desktop client و دانلود JSON

۱) روی **Create client** بزن:

![Step 5 — Create client](assets/google-setup/step-10.png)

۲) Application type را **Desktop app** بگذار (نه Web و نه iOS)، اسم مثلاً `Mac syncer`، بعد **Create**:

![Step 5 — Desktop app + name](assets/google-setup/step-11.png)

۳) در پاپ‌آپ روی **Download JSON** بزن:

![Step 5 — Download JSON](assets/google-setup/step-12.png)

### Step 6 — ذخیره به‌صورت credentials.json

فایل دانلودشده باید در پوشهٔ دادهٔ برنامه با نام **`credentials.json`** باشد. جادوگر معمولاً پیشنهاد کپی از Downloads می‌دهد؛ Confirm کن. یا از **Import credentials** همان JSON را انتخاب کن.

![Step 6 — Save credentials.json](assets/google-setup/step-13.png)

### ورود به جیمیل (token.json)

بعد از Setup، اگر دکمه **Sign in to Google** را دیدی روی آن بزن (وی‌پی‌ان شخصی هنوز روشن باشد). در مرورگر جیمیل خودت را انتخاب کن و Continue بزن.

اگر گوگل گفت برنامه verified نیست: **Advanced → Go to … (unsafe)** را بزن — برای استفادهٔ شخصی عادی است.

تا وقتی برنامه در حالت **Testing** باشد، گاهی بعد از حدود **۷ روز** لاگین گوگل منقضی می‌شود؛ آن وقت دوباره **Reauth Google** را بزن.

با **Check Google auth** می‌توانی مطمئن شوی همه‌چیز اوکی است.

---

## ۵) گرفتن ایونت‌ها و سینک

وقتی **هم Outlook و هم Google** آماده شدند:

### نشان دادن ایونت‌های Outlook

1. وی‌پی‌ان **شرکت** را روشن کن.
2. روی **Show events from outlook** بزن.
3. لیست باید در قسمت Outlook events بیاید. اگر خالی بود یا خطا داد، لاگین Outlook و وی‌پی‌ان شرکت را دوباره چک کن.

### کپی به Google Calendar

1. برای صحبت با گوگل، اگر شرکت گوگل را می‌بندد، وی‌پی‌ان **شخصی** را روشن کن.
2. روی **Sync** بزن (بعد از یک Show events موفق فعال می‌شود).
3. ایونت‌ها در تقویم گوگل با نامی که گذاشتی (پیش‌فرض **Work (Outlook)**) ظاهر می‌شوند و یک یادآور پاپ‌آپ ۱۵ دقیقه‌ای هم برای آن تقویم تنظیم می‌شود.

قبل از نوشتن واقعی می‌توانی **Sync dry-run** را بزنی تا فقط ببینی چه چیزی عوض می‌شود.

### اگر الان Outlook داری ولی بعداً می‌خواهی به گوگل بزنی

1. با وی‌پی‌ان شرکت: **Get from outlook and Store encrypted** — پسورد جدا برای فایل رمزگذاری‌شده می‌پرسد.
2. بعداً با دسترسی به گوگل: **Sync from encrypted file** — همان پسورد را بزن، بدون اینکه دوباره از Outlook بخواند.

---

## ۶) سینک خودکار (مثلاً هر ۳۰ دقیقه)

تا سیستم خودش این کار را تکرار کند:

1. در ردیف Schedule، منوی **Every** را روی **`30m`** بگذار (یا `15m` / `1h` / `3h` / `6h` / `12h`).
2. روی **Install schedule** بزن.
3. مک با **launchd** این فاصله را اجرا می‌کند. اگر یک اجرای پس‌زمینه شکست بخورد، ممکن است نوتیفیکیشن macOS ببینی.

برای توقف: **Uninstall schedule**.

نکته: برای اینکه سینک خودکار موفق باشد، وقتی زمانش رسید باید بتوانی به سرور ایمیل شرکت برسی (وی‌پی‌ان/وای‌فای شرکت) و در صورت نیاز به گوگل هم — بسته به شبکهٔت.

---

## چک‌لیست سریع

- [ ] DMG نصب شد؛ در Privacy & Security در صورت نیاز **Open Anyway** زدیم  
- [ ] در صورت پرسش Keychain، پسورد مک + **Always Allow**  
- [ ] با وی‌پی‌ان شرکت: **Login to Outlook** اوکی شد  
- [ ] با وی‌پی‌ان شخصی: **Setup Google** + **Sign in to Google** اوکی شد  
- [ ] **Show events from outlook** ایونت نشان داد  
- [ ] **Sync** به گوگل کپی کرد  
- [ ] در صورت نیاز **Every → 30m → Install schedule**

موفق باشی!

---

## اختیاری — نصب و راه‌اندازی با Terminal

> این بخش **اختیاری** است و فقط برای کسانی است که می‌خواهند از **Terminal** استفاده کنند (brew، clone، `python -m syncer setup`). اکثر کاربران همان راهنمای **DMG + اپلیکیشن گرافیکی** بالا را کافی دارند.

قبل از شروع یه چیز مهم در مورد اینترنت و وی‌پی‌ان بگم، چون تو ایران قاطی کردنش خیلی پیش میاد:

- هر جا می‌خوای به **Gmail** برسی، یا **brew** نصب کنی، یا کتابخونه‌های پایتون (`pip install`) و پروژه رو از گیت‌هاب بگیری، باید اینترنتت با **وی‌پی‌ان شخصی** باز باشه. اینترنت عادی ایران ممکنه اوکی نباشه و گیر کنی.
- هر جا باید به **ایمیل شرکتی** وصل بشی (مثلاً سرور `mail.digikala.com`)، وی‌پی‌ان شخصی رو **خاموش** کن و وی‌پی‌ان شرکت رو **روشن** کن. یا برو رو وای‌فایی که ایمیل شرکت توش باز می‌شه.

اوکیه، بریم سراغ کار.

---

اول اگه یه وی‌پی‌ان شخصی خوب داری روشنش کن (برای نصب چیزا و گوگل لازم می‌شه).

بعد باید نرم‌افزار **Terminal** رو باز کنی.

بعد، در صورتی که روی مک **brew** رو نصب نداری، تو Terminal همین دستور رو وارد کن و Enter بزن:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

صبر کن تا تموم بشه. اگه آخرش چند خط بهت گفت که باید تو `~/.zprofile` چیزی اضافه کنی، همون دستورهایی که خودش می‌ده رو کپی کن و بزن. یه نمونهٔ رایج روی مک‌های جدید اینه:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

بعد که brew به طور موفقیت‌آمیز نصب شد، این دستور رو بزن که Python 3.11 برات نصب بشه:

```bash
HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 brew install python@3.11
```

حالا باید یه فولدر درست کنی. مثلاً برای ساخت فولدری با اسم `outlook-to-gmail` روی Desktop می‌تونی این رو بزنی:

```bash
mkdir -p ~/Desktop/outlook-to-gmail
```

حالا با این دستور برو تو همون فولدر:

```bash
cd ~/Desktop/outlook-to-gmail
```

حالا این دستور رو بزن که پروژه رو از گیت‌هاب بیاره (هنوز وی‌پی‌ان شخصی روشن باشه):

```bash
git clone https://github.com/hamidhandid/outlook-to-gmail-calendar-syncer.git
```

بعد این رو بزن که بری داخل فولدری که الان دانلود شده:

```bash
cd outlook-to-gmail-calendar-syncer
```

حالا این:

```bash
python3.11 -m venv .venv
```

بعد این:

```bash
source .venv/bin/activate
```

بعد این دستور رو بزن و صبر کن نصب کامل بشه (باز هم وی‌پی‌ان شخصی لازم است):

```bash
pip install -r requirements.txt
```

وقتی تموم شد، این دستور رو بزن که وارد کارهای اولیهٔ ساخت کلندر تو اکانت گوگل بشی (وی‌پی‌ان شخصی هنوز روشن باشه چون با گوگل کار داریم):

```bash
python -m syncer setup
```

این خروجی رو می‌بینی:

```text
Outlook → Google Calendar setup wizard
======================================

This walks you through creating a personal Google Cloud project,
turning on the Calendar API, and downloading an OAuth client.
It then writes config.yaml for your Exchange server.

Press Enter to start…
```

روی کیبورد **Enter** رو بزن.

بعدش اینو می‌بینی:

```text
Google OAuth client (do this once, with the Gmail that should
receive your work calendar)
…
Step 1 — Create a Google Cloud project
…
Opening:
  https://console.cloud.google.com/projectcreate

Press Enter when that step is done…
```

تو صفحهٔ وبی که باز می‌شه یه اسم برای پروژه‌ت انتخاب کن (مثلاً `outlook-calendar-sync` می‌تونی بذاری) و Create رو بزن. از بالای صفحه هم مطمئن شو همون پروژه انتخاب شده.

بعد برگرد به Terminal و دوباره **Enter** رو بزن.

حالا این رو می‌بینی (Step 2 — Enable the Google Calendar API). تو صفحهٔ وب **Enable** رو بزن. وقتی اوکی شد برگرد به Terminal و Enter بزن.

بعد Step 3 میاد (OAuth consent / Google Auth Platform). تو GUI هر کلیک اسکرین‌شات خودش را دارد؛ تو صفحهٔ وب:

1. اگه **Get started** دیدی روش کلیک کن.
2. تو قسمت App name یه اسم بذار، مثلاً `Outlook Calendar Sync`.
3. تو User support email جیمیل خودت رو انتخاب کن و Next بزن.
4. Audience رو بذار رو **External** و Next بزن. (Internal فقط برای اکانت Workspace شرکتیه؛ جیمیل شخصی باید External باشه.)
5. تو Contact Information دوباره ایمیل خودت رو بزن و Next.
6. آخرش تیک رو بزن و Continue / Create رو بزن.

حالا برگرد به Terminal و Enter بزن.

Step 4 میاد — Add yourself as a test user. تو صفحهٔ وب تو قسمت Test users دکمهٔ **Add users** رو بزن، جیمیل خودت رو وارد کن و Save بزن. بعد برگرد Terminal و Enter.

حالا Step 5 — این یکی خیلی مهمه:

تو صفحهٔ وب **Create client** رو بزن. تو Application type حتماً گزینهٔ **Desktop app** رو انتخاب کن (Web یا iOS نزن). یه اسم بذار مثل `Mac syncer` و Create رو بزن. تو پاپ‌آپی که باز می‌شه **Download JSON** رو بزن.

برگرد Terminal و Enter بزن.

حالا چیزی شبیه این رو می‌بینی (مسیرها روی سیستم تو فرق می‌کنه):

```text
Step 6 — Save credentials.json in this project
The file must end up at:
  /Users/YOU/Desktop/outlook-to-gmail/outlook-to-gmail-calendar-syncer/credentials.json
Found a Google client file in Downloads:
  /Users/YOU/Downloads/client_secret_….apps.googleusercontent.com.json
Copy that file here as credentials.json? [Y/n]:
```

اینجا حرف **`Y`** رو وارد کن و Enter بزن.

حالا این رو می‌بینی:

```text
Exchange / Outlook connection
This computer talks to your mail server over Exchange Web Services.
Apple Mail is not required. Connect the company VPN first.
Work email address:
```

اینجا ایمیل کاری‌ت رو وارد کن. مثلاً چیزی مثل `you@digikala.com` یا `you@fidibo.com` (نه اینکه `@mail.digikala.com` بنویسی؛ اون آدرس سروره). بعد Enter.

بعد می‌پرسه:

```text
Exchange host (from OWA, without https://) [mail.digikala.com]:
```

پیش‌فرض `mail.digikala.com` است — می‌تونی فقط Enter بزنی. بعد تو قسمت username می‌تونی خالی بذاری و فقط Enter بزنی.

اگه اومد:

```text
Auth type: ntlm or basic [ntlm]:
```

باز فقط Enter بزن (بذاره روی ntlm).

بعد این خط میاد:

```text
Verify TLS certificates? Choose n if the company uses an internal CA [y/N]:
```

پیش‌فرض **`n`** است — معمولاً فقط Enter بزن (مگر گواهی عمومی معتبر داشته باشی).

بعد:

```text
Copy full details (full) or only Busy blocks (busy)? [full]:
```

پیش‌فرض **`full`** است (عنوان و جزئیات). اگه فقط Busy می‌خوای بنویس `busy` و Enter.

بعد:

```text
Name of the Google calendar to create/use [Work (Outlook)]:
```

می‌تونی فقط Enter بزنی.

بعد:

```text
Days of past events to copy [7]:
```

اینجا به اسکریپت می‌گی از چند روز قبل ایونت بیاره. یه عدد بزن، یا Enter بزن که پیش‌فرض ۷ روز باشه.

بعد:

```text
Days of future events to copy [60]:
```

همین‌طور برای روزهای آینده؛ Enter یعنی تا ۶۰ روز بعد، یا عدد دلخواهت رو بزن.

بعد این رو می‌بینی:

```text
Save the Exchange password in the system keyring now? [Y/n]:
```

روی کیبورد **`Y`** بزن و Enter.

حالا مهم: برای اینکه بتونه به ایمیل شرکت وصل بشه، وی‌پی‌ان شخصی رو **خاموش** کن و وی‌پی‌ان شرکت رو **روشن** کن (یا برو رو وای‌فایی که ایمیل شرکت توش باز می‌شه).

این رو می‌بینی:

```text
Password for you@company.com:
```

پسورد ایمیلت رو وارد کن. حواست باشه اینجا معمولاً چیزی تو Terminal نشون داده نمی‌شه، ولی تو تایپ کن؛ اوکیه، خودش می‌فهمه. بعد از تایپ Enter بزن.

بعد اینو می‌بینی:

```text
Open the Google sign-in now to test Calendar access? [Y/n]:
```

حرف **`Y`** رو تایپ کن و Enter بزن. برای این مرحله دوباره وی‌پی‌ان شخصی رو روشن کن تا جیمیل باز بشه. تو صفحهٔ وبی که باز می‌شه اکانت جیمیل خودت رو انتخاب کن و Continue رو بزن. بعد می‌تونی تب مرورگر رو ببندی. وقتی برگردی به Terminal تقریباً باید اینو ببینی:

```text
Setup finished.
```

---

از این به بعد، هر دفعه که می‌خوای کار کنی، اول Terminal رو باز کن و برو تو همون فولدر. تو این مثال فولدر این بود:

`~/Desktop/outlook-to-gmail/outlook-to-gmail-calendar-syncer`

یعنی:

```bash
cd ~/Desktop/outlook-to-gmail/outlook-to-gmail-calendar-syncer
```

بعد:

```bash
source .venv/bin/activate
```

بعد:

```bash
python -m syncer
```

یه منو با شماره می‌بینی. مثلاً عدد **۹** لیست ایونت‌هات رو نشون می‌ده (به‌طور پیش‌فرض از حدود ۷ روز قبل تا ۶۰ روز بعد). اگه ایونت‌هات رو دیدی، احتمالاً از سمت Outlook شرکت اوکیه — فقط یادت باشه برای این کار وی‌پی‌ان شرکت / وای‌فای شرکت لازم است.

بعد دوباره `python -m syncer` رو بزن و گزینهٔ **۱۱** رو انتخاب کن تا ایونت‌های Outlook بره تو گوگل‌کلندرت. اگه وسط کار با گوگل مشکل داشتی، ممکنه دوباره وی‌پی‌ان شخصی لازم بشه.

اگه الان به ایمیل شرکت دسترسی داری ولی بعداً می‌خوای بری سراغ گوگل: گزینهٔ **۱۴** (`store`) ایونت‌ها رو تو یه فایل رمزگذاری‌شده ذخیره می‌کنه؛ بعداً با گزینهٔ **۱۶** (`sync-stored`) همون فایل رو می‌فرسته به گوگل‌کلندر (بدون اینکه دوباره از Outlook بخونه).

موفق باشی!
