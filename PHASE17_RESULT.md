# Phase 1.7 — Offline verification completed

محیط توسعه و تست آفلاین برای CPython 3.12.14 روی Windows AMD64 بازتولید شد. گزارش اولیه مسدودبودن در انتهای این فایل برای سابقه آمده است.

## Wheelhouse and installation

مسیر ورودی `C:/Users/hamed/Downloads/mouod-wheelhouse` قابل‌خواندن بود و دقیقاً هفت wheel مورد انتظار و SHA256.txt را داشت. هش SHA-256 هر فایل با فایل همراه و هش انتشار مستقل PyPI مطابق بود. نام و نسخه در نام فایل و METADATA، شرط Requires-Python و تگ سازگاری با مفسر بررسی شدند. Pillow تگ cp312-cp312-win_amd64 داشت. pip وابستگی‌های مورد نیاز را فقط از همین هفت فایل حل کرد.

| نسخه تأییدشده در هر دو محیط | مرجع هش انتشار |
| --- | --- |
| Django 6.1.2 | [PyPI](https://pypi.org/project/Django/6.1.2/#files) |
| Pillow 13.0.0 | [PyPI](https://pypi.org/project/pillow/13.0.0/#files) |
| asgiref 3.12.1 | [PyPI](https://pypi.org/project/asgiref/3.12.1/#files) |
| jdatetime 6.1.1 | [PyPI](https://pypi.org/project/jdatetime/6.1.1/#files) |
| jalali-core 1.0.0 | [PyPI](https://pypi.org/project/jalali-core/1.0.0/#files) |
| sqlparse 0.6.0 | [PyPI](https://pypi.org/project/sqlparse/0.6.0/#files) |
| tzdata 2026.5 | [PyPI](https://pypi.org/project/tzdata/2026.5/#files) |

**PASS — بازتولیدپذیری.** env-a و env-b هر دو از ابتدا با مفسر Codex ساخته شدند. نصب از wheelhouse محلی با هش اجباری، pip check و import نسخه‌های Django و Pillow در هر دو موفق شد. هیچ بسته‌ای از اینترنت دانلود نشد. [manifest دارای هش](<C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase17-recovery/requirements-verified.txt>)

```powershell
python -B -m pip --isolated --disable-pip-version-check install --no-index --no-cache-dir --only-binary=:all: --require-hashes --find-links='C:/Users/hamed/Downloads/mouod-wheelhouse' -r requirements-verified.txt
python -B -m pip check
```

## Django verification

فرمان‌ها با مفسر env-a در project-check اجرا شدند. فایل SQLite آن از بکاپ فاز اول کپی شد.

| بررسی | نتیجه |
| --- | --- |
| `manage.py check` | PASS — صفر خطا و صفر بررسی خاموش |
| `manage.py check --tag urls` | PASS |
| `manage.py showmigrations --plan` | PASS — هر ۲۱ مهاجرت در کپی اعمال‌شده بود. تطابق کامل مدل با state مهاجرت جداگانه سنجیده نشد. |
| بارگذاری App و Model | PASS — ۸ App و ۲۴ مدل از رجیستری بارگذاری شدند. |
| Pillow و ImageField | PASS — Pillow تصویر PNG مصنوعی ۱×۱ ساخت و فرم متناظر TreasureItem.image آن را معتبر تشخیص داد. |

## Regression results

پیش از تست، تنها اتصال SQLite حافظه‌ای و ایمیل locmem در تنظیمات تست تأیید شدند. مهاجرت‌های runner فقط در دیتابیس حافظه‌ای اجرا شدند. تنظیمات و انتظارات تست‌های قبلی حفظ شدند.

| تست | نتیجه |
| --- | --- |
| ثبت‌نام و ورود | PASS |
| عضویت یکتای تیم | PASS |
| ارسال و تکرار درخواست مأموریت | PASS |
| تأیید، رد و تأیید دوباره مأموریت و تراکنش امتیاز و سکه | PASS |
| سؤال روزانه و پاداش یک‌باره | PASS |
| ثبت‌نام تکراری مسابقه | PASS |
| پاسخ و دریافت پاداش پایان مسابقه | PASS |
| نهایی‌سازی مسابقه و رتبه بر اساس تعداد پاسخ درست | PASS |
| خرید، ثبت تراکنش و کاهش انبار | PASS |
| رفتار فعلی مجوز داشبورد | PASS |
| انتظار امنیتی منع اعطای staff توسط staff عادی | FAIL شناخته‌شده — مقدار staff حساب هدف True شد. |

```powershell
python -B manage.py test missions.test_behavioral_baseline.BehavioralBaseline --settings=mouod.baseline_settings -v 2
python -B manage.py test missions.test_behavioral_baseline.ExpectedSecureBehavior --settings=mouod.baseline_settings -v 2
```

## Files and remaining issues

- داخل پروژه فقط PHASE17_RESULT.md به‌روزرسانی شد. هش دیتابیس اصلی قبل و بعد برابر با CC0CEAE970F104624F65B0AB8EF1C25D817213B03DBEDC141169775D64A3D00C بود. سورس، مهاجرت‌ها و رسانه‌ها ویرایش نشدند.
- بیرون پروژه در `C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase17-recovery` فایل requirements-verified.txt، دو محیط env-a و env-b و پوشه project-check با کپی missions، dashboard، mouod، manage.py و db.sqlite3 ایجاد شدند. wheelhouse ورودی فقط خوانده شد.
- مانع نصب و تست آفلاین برطرف شد. نقص مجوز شناخته‌شده باقی است. بررسی استقرار Production در این فاز انجام نشد. فاز ۲ آغاز نشد.

---

## سابقه گزارش اولیه

# Phase 1.7 — Offline Dependency Recovery

**BLOCKED — مجموعه محلی و معتبر wheel برای نسخه‌های پروژه پیدا نشد.**

| بررسی | نتیجه |
| --- | --- |
| جست‌وجوی wheelhouse | پوشه پروژه، Downloads، کش pip و Codex، پوشه Dio، پیوست‌ها و مسیرهای قابل‌خواندن خروجی Codex بررسی شدند. wheelهای pip و python_bale_bot به وابستگی‌های هدف مربوط نبودند. دو زیرپوشه نامرتبط خروجی Codex با خطای دسترسی از جست‌وجو خارج شدند. |
| بررسی کش HTTP pip | ۲۲ بدنه ZIP بررسی شد. هیچ‌کدام متادیتای WHEEL برای بسته‌های هدف نداشت. |
| اعتبارسنجی wheel و SHA-256 | BLOCKED — فایل هدف برای تأیید نام، نسخه، تگ، متادیتا یا هش موجود نبود. |
| نسخه‌های نصب‌شده در محیط جدید | BLOCKED — نسخه‌های هدف در فرمان زیر آمده‌اند و نصب آفلاین آن‌ها در این فاز تأیید نشده است. |
| نصب آفلاین و pip check | BLOCKED |
| Django check، URL، Pillow، ImageField و مهاجرت‌ها | BLOCKED |
| ۱۰ تست رفتار و تست مستقل مجوز | BLOCKED — در فاز ۱.۵ نتیجه تاریخی ۱۰ PASS و یک FAIL مجوز بود. در این فاز اجرا نشدند. |
| نصب در محیط دوم و manifest تأییدشده | BLOCKED |

## دانلود دستی در محیط مجاز

در PowerShell روی یک سیستم با **CPython 3.12 x64** و دسترسی مجاز به PyPI، فرمان‌های زیر را اجرا کنید. مسیر wheelhouse باید خالی و خارج از پروژه و کنترل نسخه باشد. pip وابستگی‌ها را با نسخه‌های صریح زیر حل می‌کند و فقط فایل wheel دریافت می‌کند.

```powershell
$wheelhouse = Join-Path $env:LOCALAPPDATA 'Mouodphase17-wheelhouse'
if (Test-Path -LiteralPath $wheelhouse) { throw 'Choose a new, empty wheelhouse path.' }
py -3.12 -c "import sys,sysconfig; assert sys.version_info[:2] == (3,12) and sysconfig.get_platform() == 'win-amd64'; print(sys.version)"
if ($LASTEXITCODE -ne 0) { throw 'CPython 3.12 x64 is required.' }
New-Item -ItemType Directory -Path $wheelhouse | Out-Null
py -3.12 -m pip download --index-url https://pypi.org/simple --only-binary=:all: --dest $wheelhouse Django==6.1.2 Pillow==13.0.0 jdatetime==6.1.1 asgiref==3.12.1 sqlparse==0.6.0 tzdata==2026.5 jalali_core==1.0.0
if ($LASTEXITCODE -ne 0) { throw 'Wheel download failed. Keep the pinned versions.' }
Get-ChildItem -LiteralPath $wheelhouse -Filter '*.whl' |
    Sort-Object Name |
    ForEach-Object { '{0}  {1}' -f (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash, $_.Name } |
    Set-Content -LiteralPath (Join-Path $wheelhouse 'SHA256.txt') -Encoding ascii
```

کل پوشه را با SHA256.txt به یک مسیر محلی خارج از پروژه منتقل کنید و مسیر آن را اعلام کنید. هش‌های فایل‌ها باید با اطلاعات انتشار منبع معتبر هم تطبیق داده شوند. پس از بررسی نسخه، تگ، وابستگی و منشأ همه فایل‌ها، نصب با `--no-index --find-links` و manifest دارای هش در دو محیط مستقل انجام می‌شود.

## فایل‌ها و حفاظت داده

فقط PHASE17_RESULT.md ایجاد شد. هش SHA-256 دیتابیس اصلی با مقدار ثبت‌شده در فاز قبل یکسان بود. هیچ نصب شبکه‌ای، فرمان Django، ساخت محیط تازه یا تغییر در فایل‌های موجود انجام نشد. فاز ۲ آغاز نشد.

