"""
rag_langchain/views.py

Endpoints:
  - POST /api/v1/rag/chat/stream/   -> existing streaming chat (LangChain)
  - POST /api/v1/rag/reindex/       -> existing reindex
  - POST /api/v1/rag/chat/          -> NEW: chat with actions (function calling)
  - GET  /api/v1/rag/health/        -> NEW: health check
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


# ==================================================================
# EXISTING VIEWS - KEEP UNCHANGED
# ==================================================================

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


# ==================================================================
# NEW: CHAT WITH ACTIONS
# ==================================================================

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

CRITICAL RULES FOR TOOL CALLING:

1. NEVER pass placeholder values like "author_handle", "user_handle",
   "article_id", "result.article_id", "result.author_handle", "example"
   as tool arguments. ALWAYS use REAL values.

2. WORK ONE ROUND AT A TIME. Do NOT chain tool calls with placeholders.
   Instead:
     - Round 1: call ONE tool (e.g. search_articles) and WAIT for the result.
     - Round 2: use the REAL values from that result for the next tool.
     - Round 3: continue if needed.

3. When the user mentions an article by TITLE (not by ID):
   - Call search_articles with the title as query.
   - The result contains the real "id" and "author_handle".
   - THEN (next round) use those REAL values for clap/bookmark/follow.

4. When the user says "follow the author" or "follow its author":
   - FIRST search_articles to find the article.
   - Look at the "author_handle" field in the result.
   - THEN call follow_user with that EXACT handle (without @).

5. When the user says "follow @username":
   - Call follow_user directly with handle="username" (remove the @).

6. For clap_article / unclap_article / bookmark_article:
   - ALWAYS use a NUMERIC article_id (e.g. 8, 12).
   - NEVER pass a title string.

EXAMPLES:

User: "Like 'How to Learn Python' and follow its author."
Round 1: search_articles(query="How to Learn Python")
         -> Result: [{"id": 8, "author_handle": "ali-ahmad", ...}]
Round 2: clap_article(article_id=8)
Round 3: follow_user(handle="ali-ahmad")

User: "Clap for article 5"
-> clap_article(article_id=5)

User: "Follow @aqib"
-> follow_user(handle="aqib")

User: "Bookmark 'Run AWS on your laptop'"
Round 1: search_articles(query="Run AWS on your laptop")
         -> Result: [{"id": 11, ...}]
Round 2: bookmark_article(article_id=11)

Rules:
- Be concise. Confirm actions with a short summary.
- Never claim an action succeeded unless the tool returned success=true.
- If a tool fails, explain why briefly and suggest a fix.
"""


def _parse_tool_args(raw_args):
    """Safely parse tool arguments from dict or JSON string."""
    if isinstance(raw_args, dict):
        return raw_args
    if isinstance(raw_args, str):
        try:
            return json.loads(raw_args)
        except json.JSONDecodeError:
            return {}
    return {}


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

    # MAX 3 ROUNDS of tool calling (multi-step support)
    MAX_ROUNDS = 3
    action_results = []

    for round_num in range(MAX_ROUNDS):
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

        # No tool call -> done, return text reply
        if not tool_calls:
            return Response({
                "reply": assistant_msg.content or "Done.",
                "action": {
                    "executed": action_results,
                    "count": len(action_results),
                } if action_results else None,
            })

        # Add assistant tool_call message to history
        messages.append({
            "role": "assistant",
            "content": assistant_msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": (
                            json.dumps(tc.function.arguments)
                            if isinstance(tc.function.arguments, dict)
                            else (tc.function.arguments or "{}")
                        ),
                    }
                } for tc in tool_calls
            ]
        })

        # Execute all tool calls in this round
        for tc in tool_calls:
            tool_name = tc.function.name
            args = _parse_tool_args(tc.function.arguments)

            logger.info(f"[Round {round_num+1}] Executing: {tool_name} args={args}")
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

    # Max rounds reached - generate final reply
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
        } if action_results else None,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def rag_health(request):
    return Response({"status": "ok", "tools": len(TOOLS_SCHEMA)})
