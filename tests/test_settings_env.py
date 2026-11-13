import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from mouod.checks import check_required_environment
from mouod.env import csv_values, env_bool, load_dotenv


class EnvironmentSettingsTests(unittest.TestCase):
    def test_csv_values_trim_whitespace_and_ignore_empty_items(self):
        self.assertEqual(
            csv_values(" localhost, 127.0.0.1 ,, "),
            ["localhost", "127.0.0.1"],
        )

    def test_boolean_values_are_explicit(self):
        self.assertTrue(env_bool(" True "))
        self.assertFalse(env_bool("FALSE"))
        with self.assertRaises(ValueError):
            env_bool("sometimes")

    def test_dotenv_parses_values_and_does_not_override_process_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(
                "# comment\nLOCAL_TEST_FROM_FILE = ' file value '\n"
                "LOCAL_TEST_FROM_PROCESS=from-file\nEMPTY_LINE\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"LOCAL_TEST_FROM_PROCESS": "process-value"}, clear=False):
                os.environ.pop("LOCAL_TEST_FROM_FILE", None)
                load_dotenv(env_file)
                self.assertEqual(os.environ["LOCAL_TEST_FROM_FILE"], " file value ")
                self.assertEqual(os.environ["LOCAL_TEST_FROM_PROCESS"], "process-value")
                os.environ.pop("LOCAL_TEST_FROM_FILE", None)


class RequiredEnvironmentCheckTests(SimpleTestCase):
    @override_settings(SECRET_KEY="")
    def test_missing_secret_key_has_actionable_system_check(self):
        errors = check_required_environment(None)
        secret_errors = [issue for issue in errors if issue.id == "mouod.E001"]
        self.assertEqual(len(secret_errors), 1)
        self.assertIn("DJANGO_SECRET_KEY", secret_errors[0].hint)

    @override_settings(DEBUG=True, CSRF_TRUSTED_ORIGINS=[])
    def test_local_debug_without_csrf_origins_has_actionable_warning(self):
        warnings = check_required_environment(None)
        csrf_warnings = [issue for issue in warnings if issue.id == "mouod.W001"]
        self.assertEqual(len(csrf_warnings), 1)
        self.assertIn("localhost:5173", csrf_warnings[0].hint)


if __name__ == "__main__":
    unittest.main()
