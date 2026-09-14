"""
rag_langchain/views.py

Endpoints:
  - POST /api/v1/rag/chat/stream/   → existing streaming chat (LangChain)
  - POST /api/v1/rag/reindex/       → existing reindex
  - POST /api/v1/rag/chat/          → NEW: chat with actions (function calling)
  - GET  /api/v1/rag/health/        → NEW: health check
"""

import json
import logging

from django.http import StreamingHttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .chain import answer_stream
from .indexing import index_all_articles
from .llm_client import get_llm_client
from .tools import TOOLS_SCHEMA, execute_tool

logger = logging.getLogger(__name__)

# EXISTING VIEWS — KEEP UNCHANGED

class ChatStreamView(APIView):
    """Existing streaming chat using LangChain RAG."""
    permission_classes = [AllowAny]
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
    """Existing reindex endpoint."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            total = index_all_articles()
            return JsonResponse({'indexed_chunks': total})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# NEW: CHAT WITH ACTIONS

SYSTEM_PROMPT = """You are "Medium Blog Assistant", a helpful AI that can:

1. Answer questions about articles on this blog.
2. Perform ACTIONS on behalf of the logged-in user:
   - publish_article       (publish a new article)
   - clap_article          (clap/like an article by ID)
   - unclap_article        (remove clap)
   - follow_user           (follow a user by handle)
   - unfollow_user         (unfollow a user)
   - bookmark_article      (save article for later)
   - search_articles       (find articles by keyword)

Rules:
- When the user asks to DO something, call the appropriate tool.
- If user asks to clap/follow/bookmark but doesn't specify WHICH article/user, ask for clarification.
- Be concise. Confirm actions with a short summary.
- If answering a question, reply normally.
- Never claim an action succeeded unless the tool returned success=true.
"""


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_with_actions(request):
    """
    POST /api/v1/rag/chat/
    Body: { "message": "...", "history": [{role, content}, ...] }
    Response: { "reply": "...", "action": {...} | null }
    """
    user_message = (request.data.get("message") or "").strip()
    history = request.data.get("history") or []

    if not user_message:
        return Response({"error": "message is required"}, status=400)

    try:
        client = get_llm_client()
    except Exception as e:
        logger.exception("LLM client init failed")
        return Response({"error": f"LLM unavailable: {e}"}, status=503)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for h in history[-10:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"]})

    messages.append({"role": "user", "content": user_message})

    try:
        resp = client.chat_with_tools(
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
            temperature=0.3,
        )
    except Exception as e:
        logger.exception("LLM call failed")
        return Response({"error": f"LLM error: {e}"}, status=502)

    choice = resp.choices[0]
    assistant_msg = choice.message

    tool_calls = getattr(assistant_msg, "tool_calls", None)
    if not tool_calls:
        return Response({
            "reply": assistant_msg.content or "",
            "action": None,
        })

    # Execute tools
    action_results = []

    messages.append({
        "role": "assistant",
        "content": assistant_msg.content or "",
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
            } for tc in tool_calls
        ]
    })

    for tc in tool_calls:
        tool_name = tc.function.name
        try:
            args = json.loads(tc.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}

        logger.info(f"Executing tool: {tool_name} args={args}")
        result = execute_tool(tool_name, args, request.user)

        action_results.append({
            "tool": tool_name,
            "args": args,
            "result": result,
        })

        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": json.dumps(result),
        })

    # Followup LLM to produce natural reply
    try:
        followup = client.chat_with_tools(
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="none",
            temperature=0.3,
        )
        final_text = followup.choices[0].message.content or "Done."
    except Exception as e:
        logger.exception("Followup LLM call failed")
        final_text = "; ".join(
            r["result"].get("message", r["result"].get("error", "Done"))
            for r in action_results
        )

    return Response({
        "reply": final_text,
        "action": {
            "executed": action_results,
            "count": len(action_results),
        }
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def rag_health(request):
    return Response({"status": "ok", "tools": len(TOOLS_SCHEMA)})