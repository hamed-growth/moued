"""Disposable file-backed SQLite tests; never connect to the project database."""
from pathlib import Path
from tempfile import TemporaryDirectory

from .baseline_settings import *  # noqa: F403

_test_database = TemporaryDirectory(prefix="imam-zaman-tests-")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {"NAME": str(Path(_test_database.name) / "test.sqlite3")},
    }
}
SILENCED_SYSTEM_CHECKS = []
