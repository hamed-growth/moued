# Project Overview

ممیزی فاز اول پروژه «امام زمان»، یک وب‌اپ فارسی تک‌استقراری Django با تیم، مأموریت، آزمون، لیگ، کیف پول و صندوق گنج. یافته‌های تجاری از خواندن کد به دست آمده‌اند و سناریوهای هم‌زمانی بازتولید نشده‌اند.

## Current Project Structure

- `mouod` تنظیمات، URL اصلی و ورودی‌های WSGI/ASGI. برنامه‌های نصب‌شده شامل missions، dashboard و admin، auth، contenttypes، sessions، messages و staticfiles از Django هستند.
- `missions` شامل ۱۹ مدل، ویوهای تابعی در views.py، فرم‌های UserRegisterForm و UserLoginForm، ثبت مدل‌ها و اقدامات پنل در admin.py و چهار مهاجرت است.
- `dashboard` شامل ویوهای تابعی، staff_required و context processor نشانگرهای داشبورد است. مستقیماً از مدل‌های missions استفاده می‌کند و مدل کاربردی مستقل ندارد.
- `missions/urls.py:8–40` قرارداد صفحات اصلی، ثبت‌نام، ورود و خروج، درخواست مأموریت، سؤال روزانه و پاسخ، فهرست/جزئیات/ثبت‌نام/شروع/بازی/پاسخ/پایان مسابقه، پروفایل، صندوق و خرید، آرشیو و لیگ را تعریف می‌کند. `dashboard/urls.py:7–41` زیر فضای نام dashboard مسیرهای کاربر و نقش‌ها، تیم و تخصیص، مأموریت و بررسی درخواست، مسابقه و نهایی‌سازی، سؤال، صندوق و تحویل، و تراکنش را تعریف می‌کند. /admin/ ورودی جداگانه است.
- قالب‌ها در missions/templates/missions، قالب پایه در missions/templates/parents و قالب‌های داشبورد در dashboard/templates/dashboard هستند. فایل‌های ایستا در missions/static شامل Bootstrap، Font Awesome، Vazirmatn، CSS و GIF هستند. رسانه‌ها در media/treasure/items هستند. یک تصویر همنام در treasure/items نیز وجود دارد.
- Git در این مسیر مخزن تشخیص نداد. وضعیت tracked، modified و untracked قابل تعیین نبود.

### مدل‌ها و روابط

| دامنه | مدل‌ها و رابطه‌ها |
| --- | --- |
| حساب | User از AbstractUser، با نقش مدیر تیم و فیلدهای موجودی |
| تیم | Team با مدیرِ User، TeamMember با FK به Team و رابطه یک‌به‌یک به User |
| مأموریت | MissionCategory؛ Mission با دسته و سازنده؛ TeamMission بین Team و Mission؛ MissionCompletion به User/Mission/Team؛ MissionRequest به User/Mission/Team و بازبین User |
| سؤال | Question؛ DailyQuestion به Question؛ DailyQuestionAnswer به User و DailyQuestion |
| مسابقه | Competition با Question از طریق CompetitionQuestion؛ CompetitionRegistration به Competition/User؛ CompetitionAnswer به Registration/Question |
| کیف پول | PointTransaction به User، شامل تغییرات امتیاز و سکه |
| صندوق | TreasureCategory؛ TreasureItem با دسته و تصویر؛ TreasurePurchase به User/Item |

## Python & Dependencies Status

محیط قدیمی برای Python 3.13.5 ثبت شده و به مفسر حساب دیگری اشاره می‌کند. دستور python سیستم قابل اجرا نبود. مفسر بسته‌بندی‌شده Codex نسخه 3.12.14 است و در محیط مستقل استفاده شد. متادیتای Django شرط >=3.12 دارد. Pillow موجود باینری cp313 Windows x64 است و با این مفسر سازگار نیست.

نسخه‌های مشاهده‌شده در dist-info شامل Django 6.1.2، asgiref 3.12.1، sqlparse 0.6.0، tzdata 2026.5، jdatetime 6.1.1، jalali_core 1.0.0، Pillow 13.0.0 و pip 26.2.2 است. این فهرست نسخه‌های نصب‌شده قدیمی است. بازتولید کامل محیط و اعتبارسنجی یک نصب تمیز انجام نشده و فایل وابستگی ایجاد نشد.

## Database & Migration Status

`mouod/settings.py:85` SQLite محلی را تنظیم می‌کند. چهار فایل 0001 تا 0004 در missions با چهار رکورد ثبت‌شده همین برنامه در بکاپ مطابق‌اند. dashboard مهاجرت کاربردی ندارد. فایل‌های pyc قدیمی با نام‌های مهاجرت اضافی دیده شدند و به‌عنوان مهاجرت منبع شمارش نشدند. بررسی سلامت SQLite روی بکاپ ok و foreign_key_check بدون سطر بود. تطابق مدل فعلی و state مهاجرت از این نتیجه قابل استنباط نیست.

## Django System Checks

دستورات Django به کپی مستقل سورس و دیتابیس محدود شدند. نتایج در بخش Verification Results آمده‌اند. هیچ migrate، makemigrations یا تستی روی پروژه اصلی اجرا نشد.

## Current Architecture Analysis

monolith فعلی از نظر استقرار یکپارچه است، اما missions مالک همه دامنه‌هاست. وابستگی dashboard به missions مستقیم و طبیعی است، ولی مرز نوشتن روشنی ندارد. از روی importهای بررسی‌شده چرخه مستقیم بین دو App مشاهده نشد. این مشاهده جایگزین اجرای importها و بررسی کامل گراف نیست.

- `missions/views.py:144,687,849` ویوهای خانه، پروفایل و لیگ چند Query و محاسبه را ترکیب می‌کنند. خواندن داده‌های رتبه‌بندی، بازه‌های شمسی و تاریخچه کاربر نامزد Selector است.
- `missions/views.py:550,1077` پاسخ مسابقه و خرید در ویو به مدل‌های متعدد می‌نویسند. Services آینده باید مجوز، اعتبارسنجی و تراکنش را یکجا مدیریت کنند.
- `missions/models.py:319,527,810` اهدای پاداش در save یا finalize پنهان است. مقداردهی موجودی و ثبت دفتر تراکنش میان چند مسیر تکرار می‌شود. صحت پاسخ مسابقه هم در views.py:630 و models.py:727 محاسبه می‌شود.
- آزمون مستقل عملیات خرید، پاداش و نهایی‌سازی دشوار است چون مسیرها با ORM، درخواست HTTP یا side effect مدل درهم تنیده‌اند. tests.py هر دو برنامه فقط اسکلت است.

## Security Findings

| شدت و محل | مشاهده | راهکار آتی و ریسک اصلاح |
| --- | --- | --- |
| High — dashboard/decorators.py:15 و dashboard/views.py:160–191 | هر staff به عملیات تغییر نقش و وضعیت کاربران دیگر دسترسی دارد. تغییر staff فقط تغییر نقش خودِ درخواست‌کننده را منع می‌کند. | مجوز جداگانه برای هر عمل و کنترل حساب هدف. ریسک بالا برای گردش‌کار کارکنان. |
| High در انتشار — mouod/settings.py:27–29 | DEBUG فعال و ALLOWED_HOSTS خالی است. | تنظیمات استقرار جدا، host صریح و کلید محیطی. ریسک متوسط خطای استقرار. |
| Medium در انتشار — missions/models.py:890 و mouod/urls.py | تصویر صندوق در Media است و در حالت توسعه سرو می‌شود. ImageField وجود دارد، ولی محدودیت سفارشی اندازه فایل و سیاست سرو مستقل در نقاط بررسی‌شده دیده نشد. | آزمون بارگذاری و محدودیت اندازه/نوع در مسیر واقعی. ریسک متوسط برای تصاویر معتبر موجود. |

Authentication از مدل سفارشی missions.User، نشست و AuthenticationMiddleware و فرم‌های Django استفاده می‌کند. CsrfViewMiddleware در settings.py:49 فعال است و عملیات POST پاسخ، خرید و مدیریت decorator دارند. پروفایل و ثبت مسابقه به request.user متکی‌اند. آزمون عملی جداسازی داده، CSRF و دسترسی نتایج انجام نشد.

## Business Logic Risks

| شدت و محل | شواهد و اثر ممکن | راهکار آتی و ریسک اصلاح |
| --- | --- | --- |
| High — missions/views.py:1082–1117 | خرید از total_points کسر می‌کند و coins تراکنش صفر است. اعتبارسنجی موجودی کاربر و انبار، کسر، ثبت تراکنش و ثبت خرید جدا هستند. خرید هم‌زمان می‌تواند باعث فروش بیش از موجودی یا ثبت چند خرید با یک کسر مؤثر شود. در مسیر ترتیبی بررسی کف موجودی وجود دارد. | خرید اتمی با کسر شرطی امتیاز و موجودی و رفتار تعریف‌شده برای retry. ریسک بالا، قرارداد مالی فعلی باید حفظ شود. |
| High — missions/models.py:21–30,319–337,405–435 | به‌روزرسانی موجودی با read-modify-write انجام می‌شود. تأیید تنها approved و رد تنها rejected را منع می‌کند. approved → rejected → approved ممکن است پاداش را دوباره ثبت کند. ذخیره وضعیت، تکمیل و تراکنش یک واحد اتمی نیستند. | گذار شرطی از pending، کلید یکتای پاداش و ثبت اتمی. ریسک بالا برای داده تاریخی و سیاست بازبینی. |
| High — missions/models.py:527–550 | finalize پیش از ثبت پاداش‌ها وضعیت finished را ذخیره می‌کند. خطای میانی می‌تواند پاداش ناقص بر جای بگذارد و بررسی وضعیت روی نمونه خوانده‌شده حفاظت هم‌زمانی ندارد. رتبه بر اساس تعداد درست و زمان پایان است. | نهایی‌سازی اتمی و قابل تکرار، تثبیت سیاست رتبه‌بندی و واجدشرایط بودن ثبت‌نام با تست. ریسک بالا برای جوایز. |
| Medium — missions/views.py:566–639 و missions/models.py:724 | عضویت سؤال در مسابقه و ثبت‌نام کاربر کنترل می‌شود و قید یکتای پاسخ هست. بررسی تعداد پاسخ، درج پاسخ و به‌روزرسانی شمارنده جدا هستند و درخواست‌های هم‌زمان می‌توانند با شمارنده ناسازگار شوند. | ثبت پاسخ و شمارنده در تراکنش واحد، کنترل سقف و مدیریت تعارض قید یکتا. ریسک متوسط برای زمان‌بندی و نتیجه مسابقه. |
| Medium — missions/models.py:801–831 | یکتایی پاسخ روزانه تعریف شده اما درج پاسخ و پاداش جداست. خطای پس از درج می‌تواند پاسخ ثبت‌شده بدون پاداش باقی بگذارد. | پاداش و ثبت پاسخ در یک تراکنش و تست retry. ریسک متوسط. |

## Technical Debt

- **Medium، خرابی مسیر آرشیو محتمل** — missions/views.py:841 قالب missions/archive.html را درخواست می‌کند و فایل در درخت بررسی‌شده وجود ندارد. بازتولید HTTP انجام نشده است. بازیابی قالب سازگار ریسک متوسط برای نمایش تاریخچه دارد.
- **Low، مسیر تکراری** — missions/urls.py:34 و :38. پاکسازی بعدی با تست reverse/resolve ریسک پایین دارد.
- **Medium، نبود خط مبنای تست و نصب** — missions/tests.py:1، dashboard/tests.py:1 و ریشه پروژه. تعریف تست‌های رفتاری و قفل وابستگی پس از تأیید محیط، ریسک پایین دارد.
- **High، مانع اعتبارسنجی کامل محیط** — venv/pyvenv.cfg و Pillow WHEEL. ساخت محیط هم‌نسخه با Python 3.13 یا تهیه wheel تأییدشده 3.12 از همان نسخه لازم است. تغییر نسخه‌ها بدون بررسی ABI و نصب تمیز ریسک متوسط دارد.

## Recommended Target Architecture

دامنه‌های Accounts، Teams، Missions، Questions، Competitions، Wallet و Treasure ابتدا در قالب ماژول‌های داخلی در monolith مرزبندی شوند. Dashboard و Admin مصرف‌کننده API داخلی Services و Selectors باشند. Wallet مالک ثبت عملیات مالی باشد و Missions/Questions/Competitions برای پاداش و Treasure برای برداشت به آن فراخوان بدهند. جابه‌جایی مدل User یا مدل‌های رابطه‌ای بین Appها ریسک تغییر app label، state مهاجرت، ContentType، permission و FK دارد.

## Safe Refactoring Roadmap

1. محیط دقیق و قابل تکرار بسازید و در کپی داده رفتار مسیرهای موجود و مجوزها را ثبت کنید.
2. با مجوز فاز بعد، Selectorهای فقط‌خواندنی را جدا کنید و قرارداد خروجی را با تست تثبیت کنید.
3. عملیات نوشتن را تدریجی در Service قرار دهید و مسیرهای وب، Dashboard و Admin را با تست‌های رفتار فعلی پوشش دهید.
4. تغییر مجوز و رفتار تجاری، تراکنش و idempotency را به تغییرات مستقل و قابل برگشت تفکیک کنید. مقادیر تاریخی را با قواعد فعلی تطبیق دهید.
5. قبل از هر جابه‌جایی مدل، روی بکاپ آزمایش state مهاجرت و داده انجام دهید. نام جدول، روابط، ContentType، مجوز و قرارداد URL معیار بررسی باشند.

## Verification Results

| بررسی | نتیجه |
| --- | --- |
| صحت بکاپ، FK و SHA-256 منبع | PASS |
| بارگذاری Django و `manage.py check --tag urls` در کپی | PASS. فقط بررسی پیکربندی URL انجام شد. |
| `manage.py check` | FAIL، fields.E210 به علت نبود Pillow سازگار. |
| `manage.py showmigrations --plan` | BLOCKED به علت fields.E210. اجرای مجدد با `--skip-checks` در کپی PASS و هر ۲۱ مهاجرت موجود در گراف اعمال‌شده بود. |
| `manage.py check --deploy` | FAIL، fields.E210، mail.E001 برای backend کنسولی و هشدارهای W004، W008، W009، W012، W016، W018 و W020 درباره HSTS، HTTPS، کلید، کوکی‌ها، DEBUG و hosts. |
| تطابق مدل با state مهاجرت، تست‌ها، مرورگر و سناریوهای هم‌زمانی | NOT TESTED. محیط وابستگی کامل نبود. تولید مهاجرت در محدوده مجاز قرار نداشت. |

**High برای انتشار** — `mouod/settings.py`، پیکربندی استقرار باید backend ایمیل عملیاتی، کلید تصادفی از محیط و سیاست HTTPS و کوکی متناسب با پراکسی داشته باشد. ریسک اصلاح متوسط تا بالا است چون کلید و HTTPS بر نشست‌ها و دسترسی کاربران اثر می‌گذارند. مقدار کلید در گزارش ثبت نشده است.

## Backup Status

بکاپ در مسیر مستقل زیر ایجاد شد. این پوشه حاوی داده پروژه و تنظیمات اصلی است.

`C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase1-backup`

- db.sqlite3 با SQLite Online Backup API از اتصال mode=ro ایجاد شد. SHA-256 فایل اصلی قبل و بعد یکسان بود.
- media با هش تک‌تک فایل‌ها بررسی شد.
- source.zip با ساختار نسبی، بررسی CRC و مقایسه بایت هر ورودی با منبع تأیید شد. محیط قدیمی، فایل‌های کش پایتون، تنظیمات ابزار و اجزایی که جداگانه بکاپ شدند از آرشیو سورس کنار گذاشته شدند.
- SHA256.txt هش فایل‌های بکاپ را ثبت می‌کند.

## Changes Made

در پروژه فقط PROJECT_AUDIT.md ایجاد شد. بیرون پروژه phase1-backup و محیط phase1-env و کپی phase1-check ایجاد شدند. کد، تنظیمات، مهاجرت‌ها، رسانه‌ها و محیط قدیمی ویرایش نشدند.

دستورات و عملیات اجراشده شامل Get-Content، Get-ChildItem، rg، git status --short، where.exe، node -v، python --version، اجرای Python -B -c برای backup و کنترل SQLite و هش، python -B -m venv --without-pip، Expand-Archive، Copy-Item برای کپی ایزوله و بسته‌های Pure Python و Get-FileHash و دستورات Django ثبت‌شده در Verification Results بود.

