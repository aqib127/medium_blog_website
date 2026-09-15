"""
rag_langchain/views.py
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

# EXISTING VIEWS

class ChatStreamView(APIView):
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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            total = index_all_articles()
            return JsonResponse({'indexed_chunks': total})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# HELPERS

def _parse_tool_args(raw_args):
    """Safely parse tool arguments. Always returns a dict."""
    if raw_args is None:
        return {}
    if isinstance(raw_args, dict):
        return raw_args
    if isinstance(raw_args, str):
        try:
            parsed = json.loads(raw_args)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, ValueError):
            return {}
    try:
        return dict(raw_args)
    except Exception:
        return {}


# SYSTEM PROMPT

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

1. EXECUTE, DON'T ASK. When the user says "do X", CALL THE TOOL. Do NOT ask
   "Would you like to?" or "Shall I?" The user's message IS the confirmation.
   The only exception: if the user's request is ambiguous (e.g. "like that
   article" without any title/ID), THEN ask for clarification.

2. NEVER pass placeholder values like "author_handle", "user_handle",
   "article_id", "result.article_id", "result.author_handle", "example"
   as tool arguments. ALWAYS use REAL values.

3. WORK MULTIPLE ROUNDS until the request is fulfilled:
   Round 1: call ONE tool (e.g. search_articles) and WAIT for the result.
   Round 2: use REAL values from the result to call the NEXT tool.
   Round 3: continue until all actions are done.

4. When the user mentions an article by TITLE (not by ID):
   - Round 1: call search_articles(title)
   - Round 2: use result's real "id" for clap_article / bookmark_article
   - Round 3: use result's "author_handle" for follow_user

5. When the user says "follow @username":
   - Call follow_user directly with handle="username" (remove @).

6. For clap_article / unclap_article / bookmark_article:
   - ALWAYS use NUMERIC article_id (e.g. 8, 12).
   - NEVER pass a title string.

EXAMPLES:

User: "Like 'Letter see soon wind learn out' and follow its author."
Round 1: search_articles(query="Letter see soon wind learn out")
   -> Result: [{"id": 96, "author_handle": "ellie.sullivan_56", ...}]
Round 2: clap_article(article_id=96)
Round 3: follow_user(handle="ellie.sullivan_56")

User: "Clap for article 5"
-> clap_article(article_id=5)

User: "Follow @aqib"
-> follow_user(handle="aqib")

DO NOT STOP after search. If the user asked for multiple actions, do ALL of them.

Rules:
- Be concise. Confirm actions with a short summary.
- Never claim success unless tool returned success=true.
"""

# NEW: CHAT WITH ACTIONS

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_with_actions(request):
    """POST /api/v1/rag/chat/"""
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

    MAX_ROUNDS = 4
    action_results = []

    for round_num in range(MAX_ROUNDS):
        # Round 1: auto (let model decide)
        # Round 2+: force tool if the LAST round had a search that found results
        if round_num == 0:
            tool_choice = "auto"
        elif action_results and any(
            r["tool"] == "search_articles" and r["result"].get("count", 0) > 0
            for r in action_results
        ):
            # If we just searched and found results, force the model to act
            tool_choice = "required"
        else:
            tool_choice = "auto"

        logger.info(f"[Round {round_num+1}] tool_choice={tool_choice}")

        try:
            resp = client.chat_with_tools(
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice=tool_choice,
                temperature=0.3,
            )
        except Exception as e:
            logger.exception("LLM call failed")
            return Response({"error": f"LLM error: {e}"}, status=502)

        choice = resp.choices[0]
        assistant_msg = choice.message
        tool_calls = getattr(assistant_msg, "tool_calls", None)

        # No tool calls - check if we have actions; if yes, return; if no, loop breaks
        if not tool_calls:
            if action_results:
                # We already did something, return final reply
                return Response({
                    "reply": assistant_msg.content or "Done.",
                    "action": {
                        "executed": action_results,
                        "count": len(action_results),
                    },
                })
            else:
                # No actions taken - return text reply
                return Response({
                    "reply": assistant_msg.content or "Done.",
                    "action": None,
                })

        # Add assistant tool_calls to history
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
                            if isinstance(tc.function.arguments, (dict, list))
                            else str(tc.function.arguments or "{}")
                        ),
                    }
                } for tc in tool_calls
            ]
        })

        # Execute tools
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
                "content": json.dumps(result, default=str),
            })

    # Max rounds reached
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
