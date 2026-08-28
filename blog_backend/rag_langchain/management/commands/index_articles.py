from django.core.management.base import BaseCommand
from rag_langchain.indexing import index_all_articles

class Command(BaseCommand):
    help = 'Index all published articles into pgvector.'

    def handle(self, *args, **options):
        total = index_all_articles()
        self.stdout.write(self.style.SUCCESS(f'Successfully indexed {total} chunks.'))
