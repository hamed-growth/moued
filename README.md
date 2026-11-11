# Imam Zaman

Persian Django application for teams, missions, daily questions, competitions and a points-funded treasure shop. Python domains live under `apps/`; the registered Django applications remain `missions` and `dashboard`. All 19 domain models, including `missions.User`, retain their original identities.

See [architecture](ARCHITECTURE.md), [domain boundaries](docs/DOMAIN_BOUNDARIES.md), [development](docs/DEVELOPMENT.md), and the [modernization report](docs/FINAL_MODERNIZATION_REPORT.md).

## Environment and verification

Use CPython 3.12 x64 and the locally verified wheels. `requirements.txt` preserves all seven pinned versions and SHA-256 hashes; the Pillow wheel targets Windows AMD64 / CPython 3.12. No additional packages are required.

```powershell
# Set this to your existing verified Python 3.12 environment.
$python = 'C:\path\outside-project\env\Scripts\python.exe'
& $python -B -m pip check
& $python -B manage.py check --settings=mouod.test_settings
& $python -B manage.py test --settings=mouod.test_settings -v 2
```

The test settings use temporary media and a disposable file-backed SQLite database, including for independent-connection concurrency tests. They never use the original database. The current verified suite has 78 tests: 71 restored historical tests and seven added contract tests.

Run a browser preview only from an independent project copy, with an SQLite Backup API copy of the database and copied media. See the development guide. The default settings are not production-ready. Passing tests do not resolve the known application defects listed in [technical debt](docs/TECHNICAL_DEBT.md).
