from django.apps import AppConfig


class PodcastConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'podcast'

    def ready(self):
        # Registers the page_published hook that writes ID3 tags.
        from . import signals  # noqa: F401
