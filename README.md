# Imam Zaman

Persian Django application for teams, missions, daily questions, competitions and a points-funded treasure shop. Domain code lives under `apps/`. Django loads `apps.web` and `apps.backoffice` with their original registry labels, `missions` and `dashboard`. All 19 models, including `missions.User`, retain their database identities.

See [architecture](ARCHITECTURE.md), [domain boundaries](docs/DOMAIN_BOUNDARIES.md), [development](docs/DEVELOPMENT.md), and the [layout migration report](docs/LAYOUT_MIGRATION.md).

## Environment and verification

Use CPython 3.12 x64 and the locally verified wheels. `requirements.txt` preserves all seven pinned versions and SHA-256 hashes; the Pillow wheel targets Windows AMD64 / CPython 3.12. No additional packages are required.

```powershell
# Set this to your existing verified Python 3.12 environment.
$python = 'C:\path\outside-project\env\Scripts\python.exe'
& $python -B -m pip check
& $python -B manage.py check --settings=mouod.test_settings
& $python -B manage.py test --settings=mouod.test_settings -v 2
```

The test settings use temporary media and a disposable file-backed SQLite database, including for independent-connection concurrency tests. They never use the original database. The current verified suite has 90 tests under `tests/`.

Run a browser preview only from an independent project copy, with an SQLite Backup API copy of the database and copied media. See the development guide. The default settings are not production-ready. Passing tests do not resolve the known application defects listed in [technical debt](docs/TECHNICAL_DEBT.md).
