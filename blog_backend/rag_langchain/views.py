import json
import logging
from django.http import StreamingHttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny  # Changed this import
from rest_framework.throttling import ScopedRateThrottle
from .chain import answer_stream
from .indexing import index_all_articles

logger = logging.getLogger(__name__)

class ChatStreamView(APIView):
    permission_classes = [AllowAny]  # Changed from IsAuthenticated
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'chatbot'

    def post(self, request):
        data = request.data
        query = data.get('message', '').strip()
        if not query:
            return JsonResponse({'error': 'No message provided.'}, status=400)

        def event_stream():
            yield f"data: {json.dumps({'type': 'start'})}\n\n"
            try:
                # We don't have a user now, so pass None or handle it
                for chunk in answer_stream(query, user=None):
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                yield f"data: {json.dumps({'type': 'end'})}\n\n"
            except Exception as e:
                logger.exception("Streaming error")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        return response

class ReindexView(APIView):
    permission_classes = [IsAuthenticated]  # Keep this authenticated

    def post(self, request):
        try:
            total = index_all_articles()
            return JsonResponse({'indexed_chunks': total})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)