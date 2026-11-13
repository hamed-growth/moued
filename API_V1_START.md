# API v1 — first working integration slice

The existing Django HTML pages and domain models remain intact. `/api/v1/` is a new, JSON-only boundary for a future React/Vue/mobile client. Nothing was migrated or deleted from the existing database.

## Install and run

Use a **copy** of the project and your own Python virtual environment. From the project root:

```bash
python -m pip install -r requirements.txt
python manage.py check
python manage.py test tests.test_api_v1 --settings=mouod.test_settings
python manage.py runserver
```

New dependency: `djangorestframework==3.18.3`, pinned with the SHA-256 checksums of PyPI's wheel and sdist. Django 6.1 is supported by DRF 3.18.x.

The sandbox that prepared this patch did not have Django installed and could not reach the Python package index, so these tests have been *authored and syntax-checked* but not executed. Do not deploy without a successful installation, Django checks, tests, and security review.

## Endpoints

| Method | URL | Login required | Meaning |
|---|---|---|---|
| GET | `/api/v1/auth/csrf/` | No | Set `csrftoken` cookie |
| POST | `/api/v1/auth/login/` | No | JSON `{ "username": "...", "password": "...", "remember_me": false }` (username may be email) |
| POST | `/api/v1/auth/register/` | No | JSON `{ "username": "...", "email": "...", "password": "..." }` |
| POST | `/api/v1/auth/logout/` | Yes | Logout; JSON body not required |
| GET | `/api/v1/me/` | Yes | Current user; no privilege/password fields |
| GET | `/api/v1/me/wallet/` | Yes | Points and coin balance |
| GET | `/api/v1/me/transactions/` | Yes | Paginated *own* transaction history |
| GET | `/api/v1/me/mission-requests/` | Yes | Paginated *own* mission requests |
| GET | `/api/v1/missions/` | Yes | Missions visible to current user's team |
| GET | `/api/v1/treasure/items/?category=gifts` | Yes | Active catalog; optional category slug |

Collections have `{ "count": N, "next": "...", "previous": "...", "results": [...] }` with page sizes 20 (default) up to 100 (`?page=2&page_size=50`). Datetimes are serialized as ISO-8601. All write operations for missions, competitions, purchases and staff actions are deliberately **not** enabled in this slice; their domain permission and replay/concurrency contracts need tests first.

## Same-origin cookie/CSRF frontend

Host the frontend and Django API on the **same origin** (a reverse proxy mapping `/api/` to Django is fine). Otherwise, you must explicitly design CORS, cookie SameSite and trusted CSRF origins; do not turn on wildcard origins or disable CSRF.

```js
const api = (path, options = {}) => fetch(`/api/v1/${path}`, {
  credentials: 'same-origin',
  ...options,
});

await api('auth/csrf/'); // establishes a csrftoken cookie
const csrf = decodeURIComponent(
  document.cookie.split('; ').find(x => x.startsWith('csrftoken='))?.split('=')[1] || ''
);
const response = await api('auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
  body: JSON.stringify({ username: 'demo', password: 'example' }),
});
if (!response.ok) throw new Error(`Login failed: ${response.status}`);
const me = await (await api('me/')).json();
const missions = await (await api('missions/')).json();
console.log(me, missions.results);
```

Note: when Django rotates the CSRF token during login, read the cookie again for the next POST. Session authentication of unauthenticated REST requests may produce HTTP 403 rather than 401; the client must check `response.ok`.

## Before production

- Configure `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, TLS and secure cookies from deployment secrets. The old development settings remain unchanged in this patch.
- Add login/registration rate limits and account-abuse protections.
- Add CORS configuration **only** when the frontend deployment domain is known.
- Test permissions for all actors and cross-account resource IDs before exposing write endpoints.
- Keep all balance adjustments in existing wallet services; API clients may never set balances or award points.
- Plan schema/OpenAPI and error format before expanding beyond phase 1.
