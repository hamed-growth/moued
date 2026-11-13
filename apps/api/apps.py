from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = "apps.api"
    verbose_name = "Public JSON API"

    def ready(self):
        from mouod import checks  # noqa: F401
