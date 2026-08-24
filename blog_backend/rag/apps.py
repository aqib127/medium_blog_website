from django.apps import AppConfig


class RagConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rag'

    def ready(self):
        # Register signals that keep the vector store in sync with articles.
        from . import signals  # noqa: F401
