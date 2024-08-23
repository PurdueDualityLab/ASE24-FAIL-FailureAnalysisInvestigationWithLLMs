from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ParametersConfig(AppConfig):
    name = "failures.parameters"
    verbose_name = _("Parameters")

    def ready(self):
        try:
            import failures.parameters.signals  # noqa F401
        except ImportError:
            pass
