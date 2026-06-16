from django.apps import AppConfig


class CusasAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cusas_app"

    def ready(self):
        from . import signals
