# زیرساخت فرانت

اجرای توسعه: `npm run dev` در پوشهٔ `front-end`. بررسی‌ها: `npm run lint` و `npm run build`.

- `src/app`: راه‌اندازی providerها، router و سبک عمومی.
- `src/pages`: ورودی سبک مسیرها. فعلاً فقط صفحهٔ اصلی وجود دارد.
- `src/widgets`: ترکیب‌های مستقل قابل استفاده در چند صفحه.
- `src/features`: کنش‌های کاربر و قابلیت‌های قابل استفادهٔ مجدد.
- `src/entities`: مدل و نمایش مفهوم‌های پایدار دامنه.
- `src/shared`: ابزار، ارتباط و UI مستقل از دامنه.

وابستگی‌ها فقط از لایهٔ بالاتر به پایین‌تر مجازند: `app → pages → widgets → features → entities → shared`. sliceهای هم‌لایه به هم وابسته نمی‌شوند. هر slice واقعی `index.js` یا `index.jsx` را به عنوان public API ارائه می‌کند؛ مصرف‌کننده وارد فایل داخلی slice نمی‌شود. `app` و `shared` به جای slice دامنه‌ای، segment دارند.

API جنگو زیر `/api/v1/` قرار دارد و از session و CSRF استفاده می‌کند. جریان محصولی برای اتصال فرانت به API هنوز تعیین نشده است؛ هنگام پیاده‌سازی آن، درخواست‌ها باید به همان مبدأ Django یا از طریق proxy به آن برسند. مسیر و فیلد جدید را بدون قرارداد backend اضافه نکنید.

## احراز هویت

`features/auth` وضعیت نشست را از `GET /api/v1/me/` می‌خواند. `AuthContext` کاربر، وضعیت `loading`/`guest`/`authenticated`/`error`، و عملیات ورود، خروج و تازه‌سازی را در اختیار فرانت می‌گذارد. `GuestGuard` مسیر عمومی را برای همه نمایش می‌دهد؛ `AuthGuard` مسیر خصوصی را تا تعیین نشست نگه می‌دارد و مهمان را به `/` (ورود) هدایت می‌کند. صفحهٔ عمومی قبلی در `/home` است. ورود و خروج ابتدا کوکی CSRF را دریافت می‌کنند. Vite مسیر `/api` را به Django روی پورت 8000 هدایت می‌کند؛ هر دو سرور را هم‌زمان اجرا کنید.

مسیرها با `createBrowserRouter` خارج از درخت React تعریف شده‌اند و از طریق `RouterProvider` اجرا می‌شوند. صفحه‌ها و guardها در route objectها ثبت می‌شوند.

چهار مسیر CSRF، ورود، ثبت‌نام و خروج در `entities/auth/api/endpoints.js` داخل شیء `authEndpoints` تعریف شده‌اند. `authService` در همان entity درخواست‌ها را اجرا می‌کند و پیش از عملیات POST کوکی CSRF می‌گیرد. `features/auth` این service را فقط از public API یعنی `entities/auth/index.js` مصرف می‌کند.
