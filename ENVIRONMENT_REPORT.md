# Environment Report

## وضعیت محیط

محیط مستقل `phase15-env` با Python 3.12.14 بسته Codex ساخته شد. محیط قدیمی به Python 3.13.5 در مسیر حساب دیگری اشاره دارد. Django 6.1.2 در متادیتای محلی Python >=3.12 را می‌پذیرد و در محیط جدید واقعاً بارگذاری شد. بسته‌های Pure Python از محیط تأییدشده فاز اول منتقل شدند. `pip list` این نسخه‌ها را نشان داد:

| بسته | نسخه محیط مستقل |
| --- | --- |
| Django | 6.1.2 |
| asgiref | 3.12.1 |
| jalali_core | 1.0.0 |
| jdatetime | 6.1.1 |
| sqlparse | 0.6.0 |
| tzdata | 2026.5 |
| pip | 25.0.1، ابزار ساخت محیط |

Pillow 13.0.0 قدیمی تگ `cp313-cp313-win_amd64` دارد. تلاش نصب دقیق همین نسخه در Python 3.12 با پیام No matching distribution found تمام شد. محیط کامل و نصب تمیز قابل بازتولید هنوز تأیید نشده‌اند و فایل requirements ساخته نشد. برای تکمیل، Python 3.13 x64 ترجیحاً 3.13.5 و بسته معتبر Pillow 13.0.0 برای همان ABI، یا wheel معتبر همان نسخه برای Python 3.12 x64 لازم است. پس از تهیه بسته سازگار، نصب دقیق و اجرای دوباره بررسی‌ها ضروری است.

## بررسی‌های Django

همه دستورهای زیر با `phase15-env/Scripts/python.exe -B` در `phase15-check` اجرا شدند. دیتابیس این پوشه کپی بکاپ فاز اول است.

| دستور | نتیجه |
| --- | --- |
| `manage.py check` | FAIL — fields.E210 روی TreasureItem.image، Pillow سازگار نصب نبود. |
| `manage.py check --tag urls` | PASS — بررسی پیکربندی URL بدون خطا. |
| `manage.py showmigrations --plan` | BLOCKED — fields.E210 قبل از چاپ برنامه. |
| `manage.py showmigrations --plan --skip-checks` | PASS — ۲۱ مهاجرت، همه ثبت‌شده در کپی. |
| تست با تنظیمات حافظه‌ای | نتیجه تفکیکی در TEST_BASELINE.md. |

## فایل‌ها و سابقه اجرا

در ریشه پروژه چهار گزارش ENVIRONMENT_REPORT.md، BUSINESS_RULES.md، TEST_BASELINE.md و PHASE2_PLAN.md و دو فایل جدید mouod/baseline_settings.py و missions/test_behavioral_baseline.py ایجاد شدند. تنظیمات تست یک بار برای رفع تعارض EMAIL_BACKEND و MAILERS اصلاح شد. هیچ فایل برنامه موجود ویرایش نشد. مقایسه بایتی ۵۸۰۷ ورودی snapshot، رسانه‌های موجود و هش SHA-256 دیتابیس اصلی موفق بود.

خارج از پروژه، محیط `phase15-env` و کپی `phase15-check` زیر مسیر زیر ساخته شدند. محیط شامل فایل‌های تولیدشده venv، pip و کپی بسته‌های جدول است. کپی پروژه شامل فایل‌های source.zip، یک نسخه از دیتابیس بکاپ و دو فایل تست است. مسیر موقت رسانه تست توسط TemporaryDirectory مدیریت شد.

`C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d`

دستورات و عملیات اجراشده در فاز ۱.۵:

- `Get-Content`، `Get-ChildItem`، `rg` و `rg --files` برای خواندن درخواست، گزارش، کد، تنظیمات و مسیرهای محیط. `Get-FileHash db.sqlite3` برای بررسی هش اولیه.
- `python.exe -B -m venv <phase15-env>` با Python 3.12.14 و `python.exe -B -m pip --disable-pip-version-check install --no-cache-dir --retries 0 --timeout 12 Pillow==13.0.0` در محیط جدید.
- `Copy-Item` برای بسته‌های موجود فاز اول و کپی بکاپ دیتابیس و فایل‌های تست، `Expand-Archive` برای سورس، `Push-Location` و `Pop-Location` برای محدودکردن اجرای Django به کپی و `Set-Content -Encoding utf8` برای ایجاد گزارش‌ها و تست.
- `python.exe -B -m pip --disable-pip-version-check list` و چهار دستور جدول بالا.
- `manage.py shell --settings=mouod.baseline_settings -c` با assertion برای تک‌بودن اتصال، SQLite حافظه‌ای برای NAME و TEST.NAME و backend ایمیل locmem. اجرای اول به تعارض تنظیمات تست رسید و اجرای دوم پس از اصلاح PASS شد. در اجرای اول هیچ تستی شروع نشد.
- دو فرمان تست در TEST_BASELINE.md. مهاجرت‌ها صرفاً توسط runner روی SQLite حافظه‌ای اعمال شدند.
- `python.exe -B -c` با hashlib و zipfile برای مقایسه snapshot سورس، رسانه و هش نهایی دیتابیس اصلی.
