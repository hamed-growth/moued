# Model and migration verification

No schema migration, model ownership change or migration rewrite was made. All 19 application models remain in `missions.models`, app label `missions`; `AUTH_USER_MODEL` remains `missions.User`. Registered applications remain Django contrib apps, missions and dashboard. Domain packages under `apps/` are not installed apps.

The pre-edit runtime snapshot records every model's table, serialized fields (including FK/M2M targets), options, bases and managers; the URL inventory; Admin model registrations; installed apps; and migration dependency inventory. `missions/contract_baseline.json` retains the identity/route contract for automated checks. Before/after runtime snapshots match exactly. A separate AST comparison confirms the only model source changes are four local service import targets.

The four original missions migrations and both migration-package initializers are byte-preserved. Fresh disposable test databases apply the historical graph successfully. In an isolated source copy, `makemigrations --check --dry-run --settings=mouod.test_settings` reports `No changes detected`.

An original-database backup was created with SQLite Backup API through a read-only source connection. A second independent copy was used for upgrade verification. `showmigrations --plan` and `migrate` reported no pending migrations. Before/after row hashes matched across all 29 tables, including content types, permissions, membership tables and migration records. SQLite `integrity_check` returned `ok`; `foreign_key_check` returned no violations. No user rows or credentials were written to the report.

## Optional model split assessment

Retain `missions/models.py`. The file's early classes are referenced by later model definitions, and completion/daily-answer save hooks reference balances and ledger models. Splitting would introduce cross-module initialization and serialization concerns without removing those coupled write policies. Existing wrappers now point to domain services through local imports. The safe domain separation is implemented independently; an internal model split is optional and deferred, not a blocker or a model-ownership migration.

## Rollback

The independent `modernization/source.zip`, `before-hashes.json`, `backup.sqlite3` and copied media live under the external evidence directory named in the final report. Verify archive entries against the pre-edit SHA-256 manifest first. Restore only paths listed as modified in `FILE_CHANGES.json`; remove only created paths listed there after checking for later user edits. The original 11 tests were absent before this task and are therefore listed as created/restored. Preserve this report if useful. Do not overwrite unchanged files or restore a database: this task does not change original data.
