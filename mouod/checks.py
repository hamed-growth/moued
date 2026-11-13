"""Actionable deployment checks for environment-backed Django settings."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.checks import Error, Warning, register


@register("security")
def check_required_environment(app_configs, **kwargs):
    issues = []
    try:
        secret_key_configured = bool(settings.SECRET_KEY)
    except ImproperlyConfigured:
        secret_key_configured = False
    if not secret_key_configured:
        issues.append(Error(
            "DJANGO_SECRET_KEY is missing or empty.",
            hint=(
                "Set a private random DJANGO_SECRET_KEY in the repository-root "
                ".env or process environment. Do not use the example placeholder."
            ),
            id="mouod.E001",
        ))
    if settings.DEBUG and not settings.CSRF_TRUSTED_ORIGINS:
        issues.append(Warning(
            "DJANGO_CSRF_TRUSTED_ORIGINS is empty while DEBUG is enabled.",
            hint=(
                "For local Vite auth, set http://localhost:5173 and "
                "http://127.0.0.1:5173 in the root .env."
            ),
            id="mouod.W001",
        ))
    return issues
