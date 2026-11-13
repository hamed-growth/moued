# Development

Use CPython 3.12 x64. The verified interpreter used for modernization is:

```text
C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase17-recovery/env-a/Scripts/python.exe
```

The project does not load `.env`. Django settings and entry points are under `mouod/`. `mouod.test_settings` is opt-in, imports the existing synthetic baseline configuration, enables Pillow checks and creates a temporary file-backed test database. Normal connections use SQLite memory, media uses a temporary directory, and mail uses locmem. Never run tests with production settings.

## Reproduce dependencies offline

```powershell
# python312 must be an existing trusted CPython 3.12 x64 interpreter.
& $python312 -m venv C:\temp\imam-zaman-env
$python = 'C:\temp\imam-zaman-env\Scripts\python.exe'
& $python -m pip install --no-index --find-links='C:\Users\hamed\Downloads\mouod-wheelhouse' --require-hashes -r requirements.txt
& $python -m pip check
```

No network fallback or version changes are part of this procedure. The current requirements hashes match the local wheels and installed versions. The environment itself was reused, not reinstalled during modernization.

## Checks

```powershell
& $python -B manage.py check --settings=mouod.test_settings
& $python -B manage.py test --settings=mouod.test_settings -v 2
& $python -B manage.py test tests.test_architecture tests.test_read_contracts --settings=mouod.test_settings -v 2
```

For migration verification, first make an isolated source copy, then run `makemigrations --check --dry-run --settings=mouod.test_settings` there. Fresh test database setup loads historical migrations. Upgrade checks must use an independent SQLite backup with settings pointing only to that backup. Never reset or fake migrations to satisfy checks.

## Preview and backups

Keep copies, environments and wheelhouses outside the source tree. Copy source, templates and static assets, excluding `.git`, tool configuration, old venv and Python caches. Open the original database using SQLite URI `mode=ro`; call `source.backup(destination)` into a separate path. Copy media independently. In the copied project's external-only settings, point `DATABASES['default']['NAME']` and `MEDIA_ROOT` to those copied paths. Verify their resolved paths before any command. Then run `check` and `runserver 127.0.0.1:8000 --noreload` with those settings. Do not run a preview against the original database.

Record SHA-256 for source, migrations, database and each media file before work. Verify zip entries against the source manifest and use SQLite integrity/foreign-key checks on the backup. Roll back source separately from data; this modernization requires no data rollback.

## Workflow

Add new reusable reads and operations to the owning domain. Keep parsing, messages and authorization at the transport boundary. Preserve conditional writes and atomic scope. Add coverage for changed contracts and independent-connection tests for transactional changes.

A Git repository now exists and was clean at task start. No repository was initialized and no commit was made. `.gitignore` prevents future additions of runtime data but does not untrack previously committed data or secrets. Before sharing a repository, review tracked files and secret history separately. For a future unversioned copy, initialize Git only after reviewing the ignore rules and selecting source files explicitly.

Production settings remain a separate deployment task: secret management, hosts, DEBUG, HTTPS, cookies, email and media serving require independent verification.
