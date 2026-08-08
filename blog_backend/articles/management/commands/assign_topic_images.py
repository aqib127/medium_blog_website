import requests
from django.core.management.base import BaseCommand
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from articles.models import Article
from articles.topic_images import build_topic_image_url


class Command(BaseCommand):
    help = (
        'Reassign every article a topic-consistent cover image based on its '
        'tags (using Picsum, deterministic per topic), replacing generic or '
        'broken placeholder images. Safe to re-run.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--only-missing',
            action='store_true',
            help='Only fill articles that currently have no image, instead of replacing all of them.',
        )

    def handle(self, *args, **options):
        only_missing = options['only_missing']
        articles = Article.objects.all().prefetch_related('tags')
        total = articles.count()
        self.stdout.write(f"Found {total} articles.")

        updated = 0
        skipped = 0
        failed = 0

        session = requests.Session()

        for index, article in enumerate(articles):
            if only_missing and article.image and article.image.name:
                skipped += 1
                continue

            tag_names = [t.name for t in article.tags.all()]
            img_url = build_topic_image_url(article.id, tag_names)

            self.stdout.write(
                f"[{index + 1}/{total}] '{article.title}' -> tags={tag_names or ['none']}"
            )

            # Picsum occasionally hiccups under bulk requests — retry a couple
            # of times before giving up on this one article and moving on.
            success = False
            last_error = None
            for attempt in range(3):
                try:
                    response = session.get(img_url, timeout=20, allow_redirects=True)
                    if response.status_code == 200 and response.content:
                        img_temp = NamedTemporaryFile(delete=True)
                        img_temp.write(response.content)
                        img_temp.flush()
                        article.image.save(f"article_{article.id}.jpg", File(img_temp), save=True)
                        success = True
                        break
                    else:
                        last_error = f"HTTP {response.status_code}"
                except requests.exceptions.RequestException as e:
                    last_error = str(e)

            if success:
                updated += 1
                self.stdout.write(self.style.SUCCESS("  -> updated"))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR(f"  -> failed: {last_error}"))

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("Done."))
        self.stdout.write(f"Updated: {updated}  Skipped: {skipped}  Failed: {failed}")
        self.stdout.write("=" * 50)