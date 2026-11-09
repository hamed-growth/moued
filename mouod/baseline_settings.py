"""Isolated baseline configuration for python manage.py test."""
from tempfile import TemporaryDirectory

from .settings import *  # noqa: F403

_test_media = TemporaryDirectory(prefix="mouod-baseline-")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {"NAME": ":memory:"},
    }
}
MEDIA_ROOT = _test_media.name
SECRET_KEY = "synthetic-test-key-for-the-behavioral-baseline"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

MAILERS = {"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}
# The baseline uses a synthetic image path and never exercises image decoding.
SILENCED_SYSTEM_CHECKS = ["fields.E210"]
