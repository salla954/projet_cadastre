from django.apps import AppConfig


class AppcadastreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = 'appcadastre'

    def ready(self):
        from . import signals  # noqa: F401
