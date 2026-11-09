# Phase 2.2 — Wallet & Treasure Transaction Safety

## Original purchase workflow and risk

The authenticated POST at missions/urls.py:35 calls buy_treasure_item. The view looked up an active item, checked numeric stock and request.user.total_points in Python, saved an absolute point balance, inserted a negative PointTransaction, saved an absolute stock value and created a pending TreasurePurchase. No transaction grouped those writes. An exception after a successful write could leave that write committed. Concurrent buyers could pass the same prechecks and overwrite the same balance or stock with stale values. These pre-fix concurrency risks were identified from source and were not reproduced against the old implementation.

The storefront sends the item ID in the URL and uses CSRF-protected POST. The Django Admin purchase form exposes purchase identity and price as read-only, and its fulfillment action and the dashboard delivery endpoint operate on existing purchases. The storefront view is the only purchase path found that deducts points and creates a purchase together.

## Implemented behavior

In missions/views.py, one transaction.atomic block now groups a conditional debit, conditional stock reservation, ledger insert and pending purchase insert. The first statement inside the transaction is a write. It deducts item.price from the current database balance using an F expression only when total_points is sufficient. The view reads that balance back for the existing response. A second conditional update verifies active status, the same price, and positive or NULL stock. Numeric stock decrements by one and SQL NULL stays NULL. Zero affected inventory rows roll back the debit and return the existing unavailable response. This also safely rejects an item that changes price during checkout.

Database errors leave the transaction before the view logs the failure and returns a generic JSON 503. No internal error appears in the response. A successful response is constructed after the atomic block exits. Each purchase still uses points, leaves coins unchanged and records one negative ledger entry and one pending purchase. Independent repeated purchases remain valid.

## Concurrency and rollback verification

| Verification | Actual result |
| --- | --- |
| Exact balance and final stock unit | 200 with balance and stock both zero, one purchase and one debit |
| Insufficient balance and insufficient stock | 400, no accounting changes |
| Unlimited stock and two consecutive purchases | Two committed purchases, stock remains NULL, coins unchanged |
| Stock reservation returning zero after the debit | 400, debit rolled back |
| Injected database exceptions after balance and stock writes | 503 in each case, all purchase changes rolled back |
| Injected database exceptions after ledger and purchase insertion | 503 in each case, all purchase changes rolled back |
| Two buyers competing for the last unit | One 200 and one 400, exactly one debit and one purchase |
| Two items competing for one buyer's last points | One 200 and one 400, one item decremented and one purchase |
| Two different items with sufficient points | Two 200 responses, two purchases and debits, final balance zero |
| Real SQLite writer lock | Worker with a connection-local zero busy timeout encountered database is locked, got JSON 503 and left no purchase changes |

The four concurrency cases used TransactionTestCase with file-backed SQLite. The three races used two separate worker connections and synchronized after initial availability reads. The lock case held an actual write transaction on the main connection. Global SQLite configuration was preserved. SQLite still serializes writers, so sufficiently long contention can yield a retryable 503. These tests establish behavior for the exercised races, and do not measure throughput or sustained contention. PostgreSQL is a future option if write contention warrants a separately tested migration.

## Duplicate requests and other remaining risks

The request contract has no idempotency key. A replay after a committed purchase, including after a lost success response, can still create a second purchase if points and stock allow it. A future compatible design could accept an optional client-generated key per intentional purchase, persist the key with a user scope and item identity, and return the prior result on replay. The schema and client changes needed for that design require separate approval. Existing non-purchase reward and administrative balance writes can still race with purchases if they save a stale absolute balance. Those paths were outside this phase.

## Test environment and results

Phase 1.7 env-a, CPython 3.12.14. pip check and manage.py check passed. Before executing tests, the sole SQLite alias, memory-only normal NAME, disposable file-backed TEST.NAME and local-memory mail backend were verified. The runner created and destroyed the isolated test database. All data fixtures were synthetic.

**32 PASS, 0 failures, 0 skipped**. This includes all 21 Phase 2.1 tests, seven purchase transaction tests and four concurrency tests. The former authorization regression remains passing. The transaction tests also check ledger amounts, coins and pending status.

Run from the isolated phase22-check copy using the Phase 1.7 interpreter:

```powershell
python -B -m pip check
python -B manage.py check
python -B manage.py test missions.test_behavioral_baseline missions.test_authorization missions.test_treasure_transactions --settings=mouod.phase22_settings -v 2
```

The phase22_settings module is present only in the isolated copy. It derives from baseline_settings and places TEST.NAME in a new TemporaryDirectory under that copy. The concurrency class requires this or equivalent disposable file-backed SQLite settings.

## Files, rollback and integrity

- Modified missions/views.py. Created missions/test_treasure_transactions.py and PHASE22_WALLET_TRANSACTION_REPORT.md. No schema or migration change is required.
- Outside the project, created phase22-check with copies of missions, dashboard, mouod, manage.py and the backup database, plus mouod/phase22_settings.py. The temporary test databases were removed by the runner.
- Verified all Phase 1 backup hashes, SQLite integrity and ZIP CRC before editing. Recorded the intended changes and an independent copy of missions/views.py in `C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase22-backup`. Its original SHA-256 was 85c477ac87f5fb85340c668f95d3dcd4f029263e1f4c1486090a7e8aa51f286c.
- For rollback, verify the backup hash, restore missions/views.py from phase22-backup and remove the added transaction test module from the reverted suite. Keep this report. No database restoration is required. The old purchase integrity risks would return.
- Original database SHA-256 remained cc0ceae970f104624f65b0ab8ef1c25d817213b03dbedc141169775d64a3d00c. Media inventory and bytes matched the backup. Phase 2.1 authorization files and tests matched their verified copy. Source snapshot comparison found only the two prior Phase 2.1 application edits and this phase's purchase view edit among archived files.
