from django.core.management.base import BaseCommand

from rag.indexing import index_all_articles


class Command(BaseCommand):
    help = 'Embed and index all published articles into the ChromaDB vector store.'

    def handle(self, *args, **options):
        self.stdout.write('Indexing published articles into ChromaDB...')
        total = index_all_articles()
        self.stdout.write(self.style.SUCCESS(f'Indexed {total} chunks.'))
