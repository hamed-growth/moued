# Environment Recovery Result — Phase 1.6

## 1. Root cause — FAIL

pip از index پیش‌فرض `https://pypi.org/simple/` استفاده کرد. درخواست مستقل HTTPS به PyPI و فرمان verbose خود pip هر دو هنگام بازکردن سوکت به `WinError 10013` رسیدند. در این اجرا پیام «No matching distribution» نتیجه دریافت‌نشدن فهرست بسته بود. محدودیت در مرحله اتصال رخ داد. پراکسی مؤثر یا تنظیم سفارشی pip در تشخیص محلی دیده نشد. شواهد اجرای پیشین برای نسبت‌دادن قطعی همان خطا به همان سیاست کافی نیست، اما خطای نصب در این فاز با علت مشخص بازتولید شد.

**PASS — ABI.** PyPI فایل رسمی `pillow-13.0.0-cp312-cp312-win_amd64.whl` را فهرست می‌کند و pip همین تگ را در محیط جدید می‌پذیرد. ناسازگاری مطرح‌شده در فاز قبل به فایل cp313 داخل venv قدیمی مربوط بود. [فایل‌های انتشار Pillow 13.0.0](https://pypi.org/project/pillow/13.0.0/#files)

## 2. Python and isolation — PASS

محیط جدید در `C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase16-env` با CPython 3.12.14، Windows AMD64، ۶۴ بیت و pip 25.0.1 ساخته شد. `include-system-site-packages = false` است. ورودی‌های python و py در PATH به WindowsApps اشاره دارند. برای ساخت محیط از مفسر بسته Codex استفاده شد.

## 3. Dependency versions — BLOCKED

نسخه‌های درخواستی Django 6.1.2، Pillow 13.0.0، jdatetime 6.1.1، asgiref 3.12.1، sqlparse 0.6.0، tzdata 2026.5 و jalali_core 1.0.0 همگی در فرمان نصب دقیق قید شدند. `pip list` فقط pip 25.0.1 را نشان داد. سازگاری مجموعه نصب‌شده قابل ارزیابی نبود.

## 4. Executed commands

- **PASS** — مفسر بسته Codex با `-B -m venv <phase16-env>`.
- **PASS** — مفسر محیط جدید با `-B -c` برای نسخه، معماری و اندازه اشاره‌گر، سپس `-m pip --version`، `-m pip debug --verbose` و `-m pip config list` با نمایش فقط نام تنظیمات. کلیدهای پراکسی و pip نیز بدون چاپ مقدار بررسی شدند.
- **FAIL** — `urllib.request.urlopen` روی `https://pypi.org/pypi/Pillow/13.0.0/json` و `python -m pip --disable-pip-version-check index versions Pillow -vv --retries 0 --timeout 10` با خطای سوکت 10013.
- **FAIL** — `python -m pip --disable-pip-version-check install --no-cache-dir --only-binary=:all: --retries 0 --timeout 12 Django==6.1.2 Pillow==13.0.0 jdatetime==6.1.1 asgiref==3.12.1 sqlparse==0.6.0 tzdata==2026.5 jalali_core==1.0.0`. resolver در اولین بسته توزیعی دریافت نکرد.
- **PASS، فقط محیط خالی** — `python -m pip check`. این نتیجه وابستگی‌های برنامه را تأیید نمی‌کند.

## 5. Django system checks

**BLOCKED** — `manage.py check`، `manage.py check --tag urls`، import Pillow و Django، بررسی ImageField و بارگذاری apps، URL و مدل‌ها در محیط تمیز به نصب وابسته بودند. هیچ دستور Django در این فاز اجرا نشد. بررسی استقرار **NOT TESTED** است و هشدارهای قبلی در PROJECT_AUDIT.md آمده‌اند.

## 6. Migration verification

**BLOCKED** — `showmigrations --plan` و بررسی تطابق مدل و مهاجرت در محیط جدید. هیچ مهاجرتی ساخته یا اعمال نشد.

## 7. Behavioral tests

**BLOCKED** — اجرای دوباره BehavioralBaseline در محیط تمیز. نتیجه تاریخی فاز ۱.۵ در TEST_BASELINE.md، ۱۰ PASS با تنظیمات تست حافظه‌ای و استثنای test-only برای fields.E210 بود. تنظیمات تست خوانده شد و تغییر نکرد.

## 8. Security test

**BLOCKED** — اجرای دوباره ExpectedSecureBehavior. نتیجه تاریخی فاز ۱.۵ یک FAIL شناخته‌شده برای اعطای staff بود. انتظار تست تغییر نکرد.

## 9. Reproducibility

**BLOCKED** — نصب نخست کامل نشد. محیط دوم و manifest تأییدنشده ایجاد نشدند. هیچ بسته‌ای از محیط دیگر کپی نشد.

## 10. Files and data

داخل پروژه فقط ENVIRONMENT_RECOVERY_RESULT.md ایجاد شد. خارج پروژه تنها phase16-env و فایل‌های تولیدشده توسط venv و pip در آن ایجاد شدند. پنج گزارش قبلی و دو فایل تست خوانده شدند. کد، رسانه و محیط قدیمی دست‌نخورده ماندند. `Get-FileHash db.sqlite3` قبل و بعد هش یکسان CC0CEAE970F104624F65B0AB8EF1C25D817213B03DBEDC141169775D64A3D00C داد. خواندن و بررسی محلی با Get-Content، Get-ChildItem، Get-Command، rg و Get-FileHash انجام شد.

## 11. Remaining blocker and readiness

**BLOCKED — آماده‌بودن محیط تمیز برای تغییرات تست‌محور تأیید نشده است.** ادامه به دسترسی مجاز pip به PyPI یا wheelhouse مورد اعتماد با همین نسخه‌ها نیاز دارد. سپس نصب تمیز، بررسی Django روی کپی ایزوله، اجرای دو مجموعه تست و تکرار نصب در محیط دوم لازم است. فاز ۲ آغاز نشد.
