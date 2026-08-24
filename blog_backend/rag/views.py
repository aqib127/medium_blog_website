import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status

from .indexing import index_all_articles
from .search import semantic_search

logger = logging.getLogger(__name__)


class ReindexView(APIView):
    """Re-embed and re-index all published articles. Admin only."""
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            total = index_all_articles()
        except Exception as exc:  # noqa: BLE001
            logger.exception('Reindex failed: %s', exc)
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'indexed_chunks': total})


class SemanticSearchView(APIView):
    """Semantic article search (RAG retrieval).

    Body: ``{"query": "...", "limit": 5}``
    """

    def post(self, request):
        query = (request.data.get('query') or '').strip()
        try:
            limit = int(request.data.get('limit', 5))
        except (TypeError, ValueError):
            limit = 5

        if not query:
            return Response({'error': 'No query provided.'}, status=status.HTTP_400_BAD_REQUEST)

        results = semantic_search(query, limit=limit)
        return Response({'results': results})
