import os
from django.core.management.base import BaseCommand
from articles.models import Article


class Command(BaseCommand):
    help = (
        "Scans every article's cover image file on disk. If the file is "
        "missing, unreadable, or zero bytes, clears the image field on that "
        "article so the API automatically falls back to a valid, "
        "topic-relevant image (via ArticleSerializer.get_image_url) instead "
        "of a broken link. Safe to re-run at any time."
    )

    def handle(self, *args, **options):
        articles = Article.objects.exclude(image='').exclude(image__isnull=True)
        total = articles.count()
        self.stdout.write(f"Checking {total} articles that have an image set...")

        cleared = 0
        ok = 0

        for article in articles:
            try:
                path = article.image.path
            except ValueError:
                # FileField has no name associated at all
                article.image = None
                article.save(update_fields=['image'])
                cleared += 1
                self.stdout.write(self.style.WARNING(f"  Cleared (no file reference): '{article.title}'"))
                continue

            if not os.path.exists(path) or os.path.getsize(path) == 0:
                article.image = None
                article.save(update_fields=['image'])
                cleared += 1
                self.stdout.write(self.style.WARNING(f"  Cleared (missing/empty file): '{article.title}'"))
            else:
                ok += 1

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("Done."))
        self.stdout.write(f"OK: {ok}   Cleared and now falling back automatically: {cleared}")
        self.stdout.write("=" * 50)