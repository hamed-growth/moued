# Implemented architecture

Imam Zaman is a Django modular monolith: one deployment and database, eight domain-oriented Python packages and two registered project applications. Model ownership remains with `missions`.

```text
apps/
  accounts/selectors/       profiles.py, overview.py
  teams/selectors/          membership.py, leagues.py, overview.py
  missions/services/       review.py
  missions/selectors/      eligibility.py, home.py
  questions/selectors/     daily.py
  competitions/services/   rewards.py
  competitions/selectors/  listing.py
  wallet/selectors/        history.py
  treasure/services/       checkout.py
  treasure/selectors/      storefront.py
  backoffice/selectors/    overview.py
common/
  calendar.py
missions/
  models.py                all 19 domain models; Django owner remains missions
  migrations/              original migration history
  views.py, forms.py       public transport and remaining workflows
  admin.py, urls.py        unchanged Admin and route contracts
  services/, selectors/    thin legacy compatibility exports
  templates/, static/      unchanged frontend assets
  test_*.py                regression and architecture contracts
  contract_baseline.json   recorded model/route identities
dashboard/
  views.py                 staff presentation; overview uses domain selector
  decorators.py            existing authorization boundary
  context_processors.py    existing menu badges
  urls.py, templates/      unchanged integration
mouod/
  settings.py, urls.py     original configuration
  asgi.py, wsgi.py         original entry points
  baseline_settings.py     historical isolated baseline
  test_settings.py         disposable file-backed SQLite tests
docs/                     development, boundaries, API plan, debt, verification
```

Every package directory has `__init__.py`. The complete current Python inventory is in `docs/PYTHON_TREE.txt`. No empty service/repository scaffolding was created. Templates/static/media were not relocated.

## Runtime flow

Public views, staff views and Admin enforce their existing request and authorization contracts. Read views call domain selectors and render the same templates/context keys. Treasure POST calls the checkout service. MissionRequest.approve/reject and Competition.finalize/CompetitionRegistration.finish retain their interfaces and delegate through local imports to domain services.

Domain services/selectors use Django ORM and `missions.models`. They do not depend on request objects, view modules, templates or dashboard presentation. Model-local imports are intentional runtime delegation; services never recurse into those wrappers. Legacy imports under `missions.services` and `missions.selectors` re-export the same objects, not copied implementations.

## Ownership and transaction guarantees

`INSTALLED_APPS` still includes missions, dashboard and Django admin/auth/contenttypes/sessions/messages/staticfiles. `AUTH_USER_MODEL` is `missions.User`. Labels, tables, relationships, migration state, content types and permissions are preserved. No `apps.*` package is registered as a Django app.

Checkout owns atomic debit/reservation/ledger/purchase. Mission review owns pending-only claim and completion creation; MissionCompletion.save retains reward side effects. Competition services own atomic finish/finalize claims and payout coordination. Conditional F-expression writes and SQLite safeguards are unchanged. There is no centralized wallet write service; daily rewards and direct model/Admin edits retain their historical semantics.

The optional internal model split was deferred: it would not resolve coupled save side effects and would expand initialization/serialization risk. Daily answer rewards, competition admission, mission reversal and wallet centralization were not forced through unresolved policy and compatibility issues.

See [domain boundaries](docs/DOMAIN_BOUNDARIES.md), [migration verification](docs/MIGRATION_REPORT.md), [API integration](docs/API_READINESS.md), [unresolved risks](docs/TECHNICAL_DEBT.md), and [executed results](docs/FINAL_MODERNIZATION_REPORT.md). Older phase reports are historical evidence, not the current module layout.

## Incremental continuation

Staff team list/detail reads now live in `apps/teams/selectors/staff.py`. See [incremental migration](docs/INCREMENTAL_MIGRATION.md); current suite: 81 passing tests.
