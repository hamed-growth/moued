from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.backoffice'
    label = 'dashboard'
    verbose_name = 'داشبورد مدیر'