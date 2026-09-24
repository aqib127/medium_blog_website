from django.apps import AppConfig


class NewsletterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'newsletter'
    verbose_name = 'Newsletter'

    def ready(self):
        # Python 3.14 + Django 4.2 compatibility patch
        try:
            from django.template.context import BaseContext, RequestContext
            import copy

            # Patch RequestContext.__copy__
            original_copy = RequestContext.__copy__

            def patched_copy(self):
                duplicate = self.__class__.__new__(self.__class__)
                # Copy all attributes manually
                for k, v in self.__dict__.items():
                    if k == 'dicts':
                        duplicate.dicts = list(v) if v else []
                    else:
                        setattr(duplicate, k, v)
                # Ensure dicts exists
                if not hasattr(duplicate, 'dicts'):
                    duplicate.dicts = []
                return duplicate

            RequestContext.__copy__ = patched_copy

        except ImportError:
            pass
