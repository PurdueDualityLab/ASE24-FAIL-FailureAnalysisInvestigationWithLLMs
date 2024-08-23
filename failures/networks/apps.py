from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NetworksConfig(AppConfig):
    name = "failures.networks"
    verbose_name = _("Networks")

    def ready(self):
        try:
            import failures.networks.signals  # noqa F401
        except ImportError:
            pass
