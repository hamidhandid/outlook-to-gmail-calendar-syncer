# راهنمای نصب اولیه (macOS) — اپلیکیشن گرافیکی

اگه انگلیسی راحت‌ترید: [First-time guide (English)](FIRST_TIME_EN.md)

این راهنما برای **نصب از فایل DMG** و کار با **پنجرهٔ برنامه** است (بدون Terminal).  
اگه برنامه‌نویس هستی و ترجیح می‌دی از Terminal نصب کنی، آخر همین فایل بخش اختیاری را ببین.

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

## پیوست اختیاری: نصب از Terminal (برای توسعه‌دهنده)

اگر نمی‌خواهی از DMG استفاده کنی:

1. وی‌پی‌ان شخصی را روشن کن؛ Homebrew و Python 3.11 را نصب کن.
2. پروژه را clone کن، venv بساز، `pip install -r requirements.txt`.
3. `python -m syncer gui` را بزن و از همین راهنمای GUI بالا ادامه بده  
   **یا** `python -m syncer setup` برای جادوی متنی در Terminal.

جزئیات brew / clone در نسخهٔ قدیمی‌تر همین فایل بود؛ مسیر پیشنهادی برای اکثر کاربران همان **DMG + پنجرهٔ برنامه** است.
