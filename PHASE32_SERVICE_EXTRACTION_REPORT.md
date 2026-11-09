# Phase 3.2 — Treasure Service Extraction

## Scope

The storefront POST at /treasure/buy/<item_id>/ is the only identified application entry point that charges points and creates a purchase. Previously buy_treasure_item handled both HTTP and the entire database operation. Dashboard and Django Admin deliver existing purchases. No reusable checkout service existed.

The storefront now calls missions.services.treasure.purchase_treasure_item(user, item_id). The service owns active-item lookup, availability checks, the transaction, stock and balance coordination, the negative ledger entry and the pending purchase. It returns (purchase, new_total). The view keeps login and POST requirements, Persian messages, HTTP status mapping and server-side database error logging.

The active-item lookup remains outside the transaction. The first write inside is the conditional F-expression debit, followed by balance refresh, conditional stock reservation at the same price, and ledger and purchase inserts. A stock conflict raises an exception out of the atomic block and rolls back the debit. Insufficient points exits the block with no affected balance rows and reports the shortfall. Database exceptions propagate after rollback. The view maps them to the existing 503. NULL stock stays NULL, coins are untouched and each deliberate purchase can succeed independently.

## Before and after

The same isolated synthetic fixture ran against the original and extracted views. The comparison matched status, redirects, exact JSON fields and text, database outcomes after success and rollback, and the sequence of SQL statement types on success.

| Case | Identical result |
| --- | --- |
| Anonymous POST | 302 to the existing login redirect |
| Authenticated GET | 405 |
| Missing or inactive item | 404 |
| Insufficient points | JSON 400 with the same shortfall |
| No stock | JSON 400 with the same unavailable message |
| Injected purchase write failure | Generic JSON 503 and zero persisted purchase effects |
| Purchase with exact points and last unit | JSON 200 with balance 0 and purchase ID, stock 0, coins 4, pending purchase and one negative ledger entry |

The existing login redirect was preserved even though its default destination was previously observed returning 404. The probe compared status for HTML errors and did not compare debug error page bytes.

## Tests

Used the Phase 1.7 offline Python 3.12.14 interpreter and phase32-check outside the source tree. The settings safety check confirmed a memory-only default database, a fresh disposable file-backed SQLite test database under that copy and locmem email. The runner removed the test database after each run.

- Baseline before editing. 61 PASS, Django check clean and pip check clean.
- Focused run. 16 PASS, including one external HTTP comparison probe, four direct service tests and all 11 existing purchase tests. Direct tests check service results, errors and rollback. Existing HTTP tests inject failures after debit, inventory, ledger and purchase writes and verify full rollback.
- The four file-backed concurrency tests used independent connections. The last item and last points cases each committed one purchase. Two funded purchases of different items both committed. A real SQLite lock produced the existing 503 without any purchase writes.
- Final suite. 65 PASS, zero failures and skips. Django reported zero issues and pip reported no broken requirements. Existing Jalali timezone warnings still appeared in unrelated profile tests.

```powershell
python -B -m pip check
python -B manage.py check --settings=mouod.phase32_settings
python -B manage.py test missions.purchase_probe missions.test_treasure_service missions.test_treasure_transactions --settings=mouod.phase32_settings -v 1
python -B manage.py test --settings=mouod.phase32_settings -v 1
```

phase32-check contains the isolated settings, probe and before.json and after.json. The database and media were not copied into this check environment.

## Files and rollback

Modified missions/views.py and ARCHITECTURE.md. Added missions/services/__init__.py, missions/services/treasure.py, missions/test_treasure_service.py and this report. The Phase 3.1 comparison and AST check confirmed that only the purchase function changed among existing view functions. Templates, URLs, models, previous tests and selectors were preserved.

Originals were independently backed up before editing in `C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase32-backup`. Verify SHA256.txt, restore both files to their matching paths and remove the two new service files and service test from the reverted code. This report may be retained. There is no data rollback.

| Original | SHA-256 |
| --- | --- |
| missions/views.py | 30178913cf6b0bb2e0bbaa1bc8ee80cdd5e963d9879fe53f124175950cbd1c9b |
| ARCHITECTURE.md | 26cfcee1f64bdd84ce4568fb8c795bd72b2ea767ebbf17ab14403e96af286296 |

The original database SHA-256 matched cc0ceae970f104624f65b0ab8ef1c25d817213b03dbedc141169775d64a3d00c before and after. Media inventory and hashes and migration inventory and bytes matched the Phase 1 backup. No migration is required.

## Limits and Phase 3.3

SQLite concurrency results cover the exercised cases. A request replay can still create another purchase if stock and points allow it. This extraction does not establish a shared Wallet service. A future approved Phase 3.3 could extract the existing pending-only Mission review operation while preserving the temporarily suspended reopening behavior and covering both dashboard and Admin entry points.
