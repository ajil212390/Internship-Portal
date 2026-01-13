from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    name = 'applications'

    def ready(self):
        # import signal handlers
        try:
            import applications.signals  # noqa: F401
        except Exception:
            pass
