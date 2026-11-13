# Final modernization report

> Historical checkpoint. The [current layout and verification](LAYOUT_MIGRATION.md) supersede its package paths.


Status: **SAFE PYTHON MODULARIZATION COMPLETED**. This is not model-ownership migration, a complete extraction of every legacy write path, or production/API deployment approval. Optional model splitting and policy-sensitive workflows are explicitly deferred.

## Original and implemented architecture

Originally, missions owned all 19 domain models and most public logic; dashboard provided staff views. Three services and two selector modules lived inside missions. The latest source had zero test files after the user's earlier removal request. The new task required the historical baseline, so all 11 archived test modules were restored byte-for-byte. Their 71 tests passed before application edits.

Eight real Python domain packages now contain three service implementation modules and twelve selector implementation modules. Calendar utilities live in common. Seven read views now delegate context construction: public home, profile, leagues, daily questions, competition list, treasure storefront and dashboard home. Large view files were reduced without moving templates, static files, routes or authentication.

Registered Django applications remain missions, dashboard and the six original contrib apps. All 19 domain models remain owned by missions, with `AUTH_USER_MODEL=missions.User`. No domain package was added to INSTALLED_APPS.

## Actual resulting structure

```text
apps/
  accounts/selectors/{profiles,overview}.py
  teams/selectors/{membership,leagues,overview}.py
  missions/services/review.py
  missions/selectors/{eligibility,home}.py
  questions/selectors/daily.py
  competitions/services/rewards.py
  competitions/selectors/listing.py
  wallet/selectors/history.py
  treasure/services/checkout.py
  treasure/selectors/storefront.py
  backoffice/selectors/overview.py
common/calendar.py
missions/
  models.py, views.py, forms.py, admin.py, urls.py
  migrations/                       unchanged
  services/, selectors/             compatibility exports
  templates/, static/               unchanged
  test_*.py, contract_baseline.json
dashboard/
  views.py, decorators.py, context_processors.py, urls.py
  templates/                        unchanged
mouod/
  settings.py, urls.py, asgi.py, wsgi.py
  baseline_settings.py, test_settings.py
README.md, requirements.txt, .env.example, .gitignore
docs/                               verification and architecture documentation
media/, db.sqlite3                   unchanged
```

Braces above abbreviate real filenames; every package has an initializer. [PYTHON_TREE.txt](PYTHON_TREE.txt) lists all 86 actual Python files, including tests and migrations, without virtualenv/cache files.

## Services, selectors and compatibility

- Treasure implementation moved to `apps.treasure.services.checkout`.
- Mission review moved to `apps.missions.services.review`.
- Competition finish/finalization moved to `apps.competitions.services.rewards`.
- Profile queries moved to accounts; league/member queries moved to teams.
- Additional existing read logic moved to mission eligibility/home, questions daily, competition listing, wallet monthly history, treasure storefront and staff overview selectors.
- Existing service/selector modules explicitly re-export identical function/exception objects. Models preserve method signatures and local delegation. Legacy view helpers remain importable.

No duplicated authoritative payout implementation remains. Transaction bodies and financial rules were retained. Model AST comparison found only four changed local import targets. Models were not split into a package; see [MIGRATION_REPORT.md](MIGRATION_REPORT.md) for the optional split assessment.

## Dependency findings and remaining responsibilities

[DEPENDENCY_GRAPH.json](DEPENDENCY_GRAPH.json) records 92 pre-edit and 147 post-edit import edges, including function-local imports and scope. Domain tests enforce no view, HTTP, template, dashboard or legacy-wrapper imports and no domain import cycles. Accounts depends on teams, wallet and calendar; teams depends on wallet/calendar; backoffice reads multiple model domains. Models delegate locally to write services without recursively calling the wrappers.

Legacy presentation retains parsing, Persian messages, HTTP method checks and permission enforcement. Registration/login, mission request creation, competition answer admission/scoring/start, team changes, daily answer rewards, fulfillment and Admin editing remain in their original paths. They were not mechanically extracted into a second set of business rules. A shared wallet writer was not introduced: it would require safely reconciling every model/Admin/reward write path. Daily rewards and answer admission need independent transactional/policy work. No optional model ownership migration was attempted.

## Verification executed

| Check | Result |
| --- | --- |
| Historical baseline before edits | 71 passed |
| Focused migrated service/transaction suite | 45 passed |
| Selector checkpoint suite | 74 passed |
| Final suite | **78 passed, zero failures, zero skips** |
| New contracts | 3 read-contract tests and 4 architecture tests |
| Django check, URL-tag check | No issues, zero silenced checks |
| pip check | No broken requirements |
| Model/table/field/FK/M2M/User and Admin identity | Before/after identical |
| URL names/patterns/callbacks | Before/after identical; development-only media route accounted for under test DEBUG=False |
| Dry-run migration state | No changes detected |
| Fresh database | Historical migrations applied by the test runner |
| Upgrade from independent backup | No pending migrations; all 29 table row hashes unchanged |
| SQLite backup health | integrity_check ok; no foreign-key violations |
| HTTP/contexts/query counts | 39 role/page snapshots identical |
| Original database, media, migration and UI hashes | Unchanged |

All behavior/concurrency tests ran on a disposable file-backed SQLite database outside application source. The original database was only read for hashing and read-only SQLite backup. Tests never connected to it. The existing Phase 1.7 CPython 3.12.14 environment was reused; no dependencies were downloaded/installed/upgraded. All seven installed versions and local wheel hashes matched the verified requirements copied to the project.

The final suite includes 11 existing independent-connection concurrency tests: four purchase cases (last stock, last funds, funded parallel purchases, real lock), two mission review races, and five competition cases (two finalizers, two finishers, finish versus finalization, real lock and characterization of late-answer admission). Those scenarios pass; the late-answer characterization passing does not mean that defect is fixed.

One initial new architecture assertion failed because Django disables DEBUG during tests and omits the development media route. The assertion now compares all application/Admin routes while handling that conditional route explicitly. Initial read probes also exposed the existing daily-template NoReverseMatch; the characterization records that known failure instead of claiming a functioning page. No historical test assertions were edited.

## HTTP and performance evidence

The recorded GET matrix spans 13 pages for anonymous, ordinary and staff users. It compares statuses, redirect destinations, template names, normalized context and SQL counts. Existing 71 tests separately cover financial POST JSON/messages, permission behavior, rollback and Admin operations. This is evidence for exercised contracts, not an exhaustive browser/UI or load test.

Observed before/after SQL counts: ordinary home 11/11, profile 20/20, league 10/10, competition listing 6/6, storefront 7/7; staff dashboard home 24/24. No optimization is claimed. The daily page with a real synthetic question returns the same 500 from a missing leaderboard URL before and after. See [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) for scalability opportunities and unchanged defects.

## Integrity, files and rollback

Original db.sqlite3 SHA-256: `cc0ceae970f104624f65b0ab8ef1c25d817213b03dbedc141169775d64a3d00c`.

5792 protected files matched their pre-edit hashes, including 2 media files, 6 migration source/initializer files and 5776 template/static files. Original migration inventory is unchanged; restored test files match their archive exactly. No original files were deleted.

Independent evidence and rollback directory:

`C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/modernization`

It contains verified source.zip, before-hashes.json, SQLite Backup API backup.sqlite3, copied media, isolated check project, upgrade backup, baseline/services/selector/final logs, identity snapshots, HTTP snapshots and after-hashes.json. It is outside source and version control. Source archive CRC and each entry's SHA-256 were checked against the source before editing. See SHA256.txt in that directory for evidence hashes.

Exact created and modified paths are recorded in [FILE_CHANGES.json](FILE_CHANGES.json). 66 files were created (including 11 restored tests); 9 existing files modified. Deliberately unchanged: all URLs, forms, Admin code, authorization decorators, original settings, migration files, templates, CSS/JS/fonts, database and media. Models changed only their four service import targets. No Git initialization, commit or environment change occurred.

Rollback: verify source.zip entries with before-hashes.json, check that current changed-file hashes still match after-hashes.json (to avoid overwriting subsequent edits), restore only the listed modified paths and remove only listed created paths. Do not restore the original database or media; they were not modified. Affected-file rollback requires no migration. Keep the evidence private because the independent backup contains original project data/configuration.

## Remaining risks and future API

All eight mandated risks remain: competition late answers, mission reopening/reversal, purchase replay, historical attribution, staff activation policy, Jalali timezone semantics, SQLite contention and production configuration. Also retained: Admin view-only finalization permission gap, login next redirect, missing default login/archive route/template behavior, daily leaderboard reverse failure, daily reward atomicity and direct financial model edits.

A future authorized `/api/v1/` layer can call these services/selectors after authentication, object authorization and validation, with allowlisted serializers and existing domain errors. No DRF, React, API routes, UI redesign, new business features or production changes were made. [API_READINESS.md](API_READINESS.md) distinguishes reusable operations from workflows still requiring design and coverage.

Completion: all safe modularization checkpoints and verification completed. Optional model splitting and broader financial/policy redesign are deliberately excluded; unresolved product/security risks prevent claiming production readiness.
