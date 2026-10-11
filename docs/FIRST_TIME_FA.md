# راهنمای نصب اولیه (macOS)

اگه انگلیسی راحت‌ترید: [First-time guide (English)](FIRST_TIME_EN.md)

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

بعد Step 3 میاد (OAuth consent / Google Auth Platform). تو صفحهٔ وب:

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
Exchange host (from OWA, without https://) [mail.company.com]:
```

برای دیجی‌کالا می‌تونی بزنی:

```text
mail.digikala.com
```

و Enter. بعد تو قسمت username می‌تونی خالی بذاری و فقط Enter بزنی.

اگه اومد:

```text
Auth type: ntlm or basic [ntlm]:
```

باز فقط Enter بزن (بذاره روی ntlm).

بعد این خط میاد:

```text
Verify TLS certificates? Choose n if the company uses an internal CA [Y/n]:
```

حرف **`n`** رو وارد کن و Enter بزن.

بعد:

```text
Copy full details (full) or only Busy blocks (busy)? [busy]:
```

اگه می‌خوای عنوان و جزئیات ایونت‌هات کامل بیاد بنویس `full` و Enter. اگه فقط می‌خوای وقتت Busy نشون داده بشه، Enter بزن یا بنویس `busy`.

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

موفق باشی!
