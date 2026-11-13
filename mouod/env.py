"""Small, dependency-free loader for project-local environment settings."""

import os
from pathlib import Path


def load_dotenv(path):
    """Load KEY=VALUE lines without replacing variables from the process."""
    env_path = Path(path)
    if not env_path.is_file():
        return

    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if not key or key in os.environ:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ[key] = value


def csv_values(value):
    """Parse a comma-separated environment value, trimming empty entries."""
    return [item.strip() for item in value.split(",") if item.strip()]


def env_bool(value):
    """Parse common explicit boolean spellings."""
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    raise ValueError(f"Invalid boolean environment value: {value!r}")
