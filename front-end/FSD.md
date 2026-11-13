# زیرساخت فرانت

اجرای توسعه: `npm run dev` در پوشهٔ `front-end`. بررسی‌ها: `npm run lint` و `npm run build`.

- `src/app`: راه‌اندازی providerها، router و سبک عمومی.
- `src/pages`: ورودی سبک مسیرها. فعلاً فقط صفحهٔ اصلی وجود دارد.
- `src/widgets`: ترکیب‌های مستقل قابل استفاده در چند صفحه.
- `src/features`: کنش‌های کاربر و قابلیت‌های قابل استفادهٔ مجدد.
- `src/entities`: مدل و نمایش مفهوم‌های پایدار دامنه.
- `src/shared`: ابزار، ارتباط و UI مستقل از دامنه.

وابستگی‌ها فقط از لایهٔ بالاتر به پایین‌تر مجازند: `app → pages → widgets → features → entities → shared`. sliceهای هم‌لایه به هم وابسته نمی‌شوند. هر slice واقعی `index.js` یا `index.jsx` را به عنوان public API ارائه می‌کند؛ مصرف‌کننده وارد فایل داخلی slice نمی‌شود. `app` و `shared` به جای slice دامنه‌ای، segment دارند.

API جنگو زیر `/api/v1/` قرار دارد و از session و CSRF استفاده می‌کند. `shared/api` پیشوند درخواست را از `VITE_API_BASE_URL` می‌گیرد (پیش‌فرض `/api/v1`) و Vite در توسعه `/api` را به مقصد `API_PROXY_TARGET` می‌فرستد. درخواست‌های مرورگر همواره به همان مبدأ فرانت‌اند می‌روند. مسیر و فیلد جدید را بدون قرارداد backend اضافه نکنید.

## احراز هویت

`features/auth` وضعیت نشست را از `GET /api/v1/me/` می‌خواند. `AuthContext` کاربر، وضعیت `loading`/`guest`/`authenticated`/`error`، و عملیات ورود، خروج و تازه‌سازی را در اختیار فرانت می‌گذارد. `GuestGuard` مسیر عمومی را برای همه نمایش می‌دهد؛ `AuthGuard` مسیر خصوصی را تا تعیین نشست نگه می‌دارد و مهمان را به `/` (ورود) هدایت می‌کند. صفحهٔ عمومی قبلی در `/home` است. ورود و خروج ابتدا کوکی CSRF را دریافت می‌کنند. برای توسعه هر دو سرور را هم‌زمان اجرا کنید؛ راهنمای env در `README.md` است.

مسیرها با `createBrowserRouter` خارج از درخت React تعریف شده‌اند و از طریق `RouterProvider` اجرا می‌شوند. صفحه‌ها و guardها در route objectها ثبت می‌شوند.

چهار مسیر CSRF، ورود، ثبت‌نام و خروج در `entities/auth/api/endpoints.js` داخل شیء `authEndpoints` تعریف شده‌اند. `authService` در همان entity درخواست‌ها را اجرا می‌کند و پیش از عملیات POST کوکی CSRF می‌گیرد. `features/auth` این service را فقط از public API یعنی `entities/auth/index.js` مصرف می‌کند.

رابط فعلی با MUI ساخته شده است. `app/theme` رنگ‌ها، فونت، جهت RTL و متن‌های فارسی `faIR` را تعریف می‌کند؛ `app/providers` کش Emotion با افزونهٔ RTL را نصب می‌کند. فرم ورود از React Hook Form و `Controller` برای فیلدهای MUI استفاده می‌کند.
