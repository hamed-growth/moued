# Project architecture

Imam Zaman is a Django modular monolith. Each domain owns its Python models, operations, queries and presentation code. The Django integration packages connect those domains to the existing database and route namespaces.

```text
apps/
  accounts/       User, account forms, login/profile, staff account operations
  teams/          Team, membership, league, staff team pages
  missions/       Mission models, request, review, assignment and completion
  questions/      Question bank, daily answers and reward workflow
  competitions/   Competition models, participation and prizes
  wallet/         PointTransaction, balances, history and reports
  treasure/       Inventory, checkout and delivery
  backoffice/     Dashboard routes, layout, authorization and shared reporting
  web/            Public routes, shared templates and static files,
                  model registration, Admin discovery and migration history
common/           Jalali calendar utilities
mouod/            Django settings and entry points
tests/            Regression and architecture contracts
media/            Uploaded media
```

`apps.missions` is the domain for mission requests, review, assignment and completion. Its `models.py` defines only mission models. Other model classes live in their owning domain packages. `apps.web.models` loads those classes for Django at startup.

The installed Django application at `apps.web` has the label `missions`. The application at `apps.backoffice` has the label `dashboard`. Those labels preserve existing tables, migration records, permissions and content types. For example, Python imports `User` from `apps.accounts.models` and Django resolves it as `missions.User`. The public URL namespace is `missions`, the staff namespace is `dashboard`, and Admin still uses names such as `admin:missions_user_change`.

For any domain, the public entry points are in `views.py`, staff entry points are in `staff_views.py`, and Django Admin definitions are in `admin.py`, where applicable. Those entry points handle HTTP and permissions and call the domain services and selectors. Services coordinate writes and selectors assemble reads. Model methods retain persistence and validation behavior. Shared UI assets live with the public or dashboard integration package, and the template names and static URLs are preserved.

Competition services own participation, scoring updates and administrative status changes. Mission completion and daily answer grading run in domain services called by their model save hooks, so direct model and Admin callers follow the same rules. Reward and checkout workflows use the wallet services for balance changes and ledger entries. Each workflow owns its transaction and decides what to credit or debit.

See [domain boundaries](docs/DOMAIN_BOUNDARIES.md), [development](docs/DEVELOPMENT.md) and [layout migration verification](docs/LAYOUT_MIGRATION.md). Earlier phase reports record historical layouts.
