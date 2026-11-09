# Development Guide

Use CPython 3.12 x64 on Windows for the verified wheel set. Phase 1.7 used Python 3.12.14 and Django 6.1.2. This working directory has no Git metadata and the legacy venv is machine-specific. Another developer needs a source export or repository access, a compatible interpreter, the verified wheelhouse and the matching hash-pinned manifest. Keep production databases and uploaded media outside development copies.

The verified environment and manifest are in `C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase17-recovery`. The manifest is external to the source tree. The local wheelhouse is C:/Users/hamed/Downloads/mouod-wheelhouse. On a different machine, obtain both from the approved distribution and verify the hashes. See [Phase 1.7](PHASE17_RESULT.md).

## Install from the verified wheelhouse

Set these paths for the current machine, then use the verified offline install command.

```powershell
$wheelhouse = 'C:/Users/hamed/Downloads/mouod-wheelhouse'
$manifest = 'C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase17-recovery/requirements-verified.txt'
$envDir = Join-Path $env:LOCALAPPDATA 'Mouod/dev-env'
py -3.12 -m venv $envDir
$python = Join-Path $envDir 'Scripts/python.exe'
& $python -B -m pip --isolated --disable-pip-version-check install --no-index --no-cache-dir --only-binary=:all: --require-hashes --find-links $wheelhouse -r $manifest
& $python -B -m pip check
```

On this machine, the existing verified interpreter is `C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase17-recovery/env-a/Scripts/python.exe`. It can be reused without installation. A clean checkout cannot execute the offline command without obtaining the external manifest and wheels.

## Test safely

Work in a disposable source copy outside the original project. Copy the code, templates and static assets while omitting db.sqlite3, media and the old venv. The project includes mouod/baseline_settings.py for memory-only tests and locmem mail. The complete concurrency suite requires file-backed SQLite. Phase 3.5 ran the following in its isolated copy.

```powershell
& $python -B -m pip check
& $python -B manage.py check --settings=mouod.phase35_settings
& $python -B manage.py test --settings=mouod.phase35_settings -v 1
```

The phase35_settings module is external and can be found in `C:/Users/hamed/.codex/visualizations/2026/11/09/01a1c163-17fb-7302-ba54-ec36dc68114d/phase35-check/mouod/phase35_settings.py`. For a new disposable checkout, use an equivalent local module that imports baseline_settings and points DATABASES["default"]["TEST"]["NAME"] to a fresh absolute SQLite path inside a TemporaryDirectory outside the original source. Keep the ordinary NAME as :memory:, the email backend as locmem, and MEDIA_ROOT temporary. Confirm all database aliases and file paths before running tests. Use synthetic accounts and data. Existing Jalali timezone warnings may appear.

## Run a local preview

In the disposable copy, confirm manage.py, the settings module and the resolved SQLite and media paths are under the intended preview root. For a fresh synthetic preview only, run migrate against the new local database. For a preview that requires existing data, use the SQLite Backup API from a read-only source connection, then copy the required media to the preview root and verify both paths. Use the actual /login/ route for manual sign-in. Create any preview users only in the disposable database.

```powershell
& $python -B manage.py check
& $python -B manage.py runserver 127.0.0.1:8000 --noreload
```

Default settings resolve SQLite and media relative to BASE_DIR. Static files are delivered by Django in local DEBUG mode. This project has no verified environment-variable settings overlay. Production needs environment-backed configuration, DEBUG disabled, hosts, HTTPS and cookie policies, production mail and separate delivery of collected static files and uploaded media. See [Django's deployment checklist](https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/).

For backup and recovery, use SQLite's Backup API for a consistent database copy, verify integrity_check and foreign_key_check, and hash the database, media and source archive. Store them separately from working files. Verify hashes before a restore rehearsal and restore to a disposable location first. Confirm media paths, migration state and regression tests there before any approved production operation. See [the Phase 1 backup record](PROJECT_AUDIT.md).
