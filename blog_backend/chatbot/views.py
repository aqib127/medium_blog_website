import json
import logging
import re
from django.conf import settings
from django.db.models import Q, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import status

import anthropic

from . import utils
from articles.models import Article, Tag
from users.models import User
from rag.search import semantic_search
from rag.generate import answer_with_rag

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------
# Tool definitions (12 functions + 1 for website info)
# --------------------------------------------------------------------
TOOLS = [
    {
        "name": "search_articles",
        "description": "Search for articles matching a query (by title, dek, body, or tag).",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Maximum number of results", "default": 10}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_article",
        "description": "Get detailed information about a specific article by its numeric ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "article_id": {"type": "integer", "description": "Numeric ID of the article"}
            },
            "required": ["article_id"]
        }
    },
    {
        "name": "search_articles_semantic",
        "description": "Semantically search articles by meaning (vector/RAG retrieval). Use for open-ended or topic questions where keyword matching may miss relevant articles. Returns title, author, tags, snippet, and relevance score.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The question or topic to search for"},
                "limit": {"type": "integer", "description": "Maximum number of results", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_user_profile",
        "description": "Get public profile of a user by their handle (username).",
        "input_schema": {
            "type": "object",
            "properties": {
                "handle": {"type": "string", "description": "User's handle (username)"}
            },
            "required": ["handle"]
        }
    },
    {
        "name": "get_user_followers",
        "description": "List followers of a user by handle.",
        "input_schema": {
            "type": "object",
            "properties": {
                "handle": {"type": "string", "description": "User's handle"}
            },
            "required": ["handle"]
        }
    },
    {
        "name": "get_user_following",
        "description": "List users followed by a user by handle.",
        "input_schema": {
            "type": "object",
            "properties": {
                "handle": {"type": "string", "description": "User's handle"}
            },
            "required": ["handle"]
        }
    },
    {
        "name": "get_user_bookmarks",
        "description": "Get the current user's bookmarked articles. Requires authentication.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_user_comments",
        "description": "Get the current user's comments. Requires authentication.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_trending_articles",
        "description": "Get trending articles by claps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of articles", "default": 5}
            }
        }
    },
    {
        "name": "get_featured_article",
        "description": "Get the featured article.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_articles_by_tag",
        "description": "Get articles by a specific tag slug.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tag_slug": {"type": "string", "description": "Tag slug"}
            },
            "required": ["tag_slug"]
        }
    },
    {
        "name": "search_users",
        "description": "Search users by name or handle.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 10}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_all_tags",
        "description": "Get list of all tags.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_website_info",
        "description": "Return a comprehensive description of the website, its features, and how to use them.",
        "input_schema": {"type": "object", "properties": {}}
    }
]

TOOL_MAP = {
    'search_articles': utils.search_articles,
    'search_articles_semantic': semantic_search,
    'get_article': utils.get_article,
    'get_user_profile': utils.get_user_profile,
    'get_user_followers': utils.get_user_followers,
    'get_user_following': utils.get_user_following,
    'get_user_bookmarks': utils.get_user_bookmarks,
    'get_user_comments': utils.get_user_comments,
    'get_trending_articles': utils.get_trending_articles,
    'get_featured_article': utils.get_featured_article,
    'get_articles_by_tag': utils.get_articles_by_tag,
    'search_users': utils.search_users,
    'get_all_tags': utils.get_all_tags,
    'get_website_info': utils.get_website_info,
}

# --------------------------------------------------------------------
# Configuration – Anthropic (if key is set) or mock
# --------------------------------------------------------------------
ANTHROPIC_API_KEY = getattr(settings, 'ANTHROPIC_API_KEY', '')
USE_MOCK = getattr(settings, 'USE_MOCK_CHATBOT', False) or not ANTHROPIC_API_KEY

client = None
model_name = None

if ANTHROPIC_API_KEY and not USE_MOCK:
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        model_name = "claude-3-5-sonnet-20241022"
        logger.info(f"Anthropic client initialized with model: {model_name}")
    except Exception as e:
        logger.error(f"Anthropic initialization error: {e}")
        USE_MOCK = True

if USE_MOCK:
    logger.warning("Chatbot running in MOCK mode.")

def get_mock_response(message, user=None):
    msg = message.lower().strip()

    # --- Greetings ---
    if re.search(r'^(hi|hello|hey|good morning|good afternoon|good evening|howdy|greetings|hey there)', msg):
        return "Hello! How can I assist you today? You can ask me about articles, authors, tags, bookmarks, and more."

    # --- Count queries ---
    if re.search(r'how many articles|number of articles|article count', msg):
        count = Article.objects.filter(status='published').count()
        return f"There are {count} published articles on this site."

    if re.search(r'how many tags|number of tags|tag count', msg):
        count = Tag.objects.count()
        return f"There are {count} tags available."

    if re.search(r'how many users|number of users|user count', msg):
        count = User.objects.count()
        return f"There are {count} registered users."

    # --- "Any more" ---
    if re.search(r'(any more|more articles|show more|list more|additional)', msg):
        articles = Article.objects.filter(status='published').order_by('-published_at')[5:10]
        if articles:
            lines = '\n'.join([f"- {a.title} by {a.author.name}" for a in articles])
            return f"Here are more articles (next 5):\n{lines}\n\nTo see different ones, ask for 'articles about [topic]' or 'latest articles' again."
        else:
            return "I've shown you all available articles. Try asking about a specific topic."

    # --- Trending ---
    if re.search(r'trending|popular|most claps', msg):
        articles = utils.get_trending_articles(limit=5)
        if articles:
            lines = '\n'.join([f"- {a['title']} by {a['author']} ({a['claps']} claps)" for a in articles])
            return f"Here are the current trending articles:\n{lines}"
        return "No trending articles found at the moment."

    # --- Featured ---
    if re.search(r'featured|highlight', msg):
        art = utils.get_featured_article()
        if art:
            return f"The featured article is '{art['title']}' by {art['author']}. Summary: {art['dek']}"
        return "No featured article is currently available."

    # --- Latest ---
    if re.search(r'latest|newest|recent', msg):
        articles = Article.objects.filter(status='published').order_by('-published_at')[:5]
        if articles:
            lines = '\n'.join([f"- {a.title} by {a.author.name}" for a in articles])
            return f"Here are the latest articles:\n{lines}"
        return "No published articles found."

    # --- Author of a specific article ---
    author_match = None
    if not author_match:
        author_match = re.search(r"who is author ['\"](.+?)['\"]", msg)
    if not author_match:
        author_match = re.search(r"who is the author of ['\"](.+?)['\"]", msg)
    if not author_match:
        author_match = re.search(r"who (?:is|wrote) ['\"](.+?)['\"]", msg)
    if not author_match:
        author_match = re.search(r"author of ['\"](.+?)['\"]", msg)
    if not author_match:
        author_match = re.search(r"author of\s+(.+)", msg)
    if not author_match:
        author_match = re.search(r"who (?:is|wrote)\s+(.+)", msg)

    if author_match:
        title_query = author_match.group(1).strip().strip('"\'')
        if title_query:
            article = Article.objects.filter(Q(status='published') & Q(title__icontains=title_query)).first()
            if article:
                return f"The article '{article.title}' was written by {article.author.name}."
            article = Article.objects.filter(Q(status='published') & (Q(dek__icontains=title_query) | Q(body__icontains=title_query))).first()
            if article:
                return f"The article '{article.title}' (contains '{title_query}' in its content) was written by {article.author.name}."
            article = Article.objects.filter(Q(status='published') & Q(title__iexact=title_query)).first()
            if article:
                return f"The article '{article.title}' was written by {article.author.name}."
            cleaned = re.sub(r'^(the|a|an)\s+', '', title_query, flags=re.I)
            if cleaned and cleaned != title_query:
                article = Article.objects.filter(Q(status='published') & Q(title__icontains=cleaned)).first()
                if article:
                    return f"The article '{article.title}' was written by {article.author.name}."
            return f"Sorry, I couldn't find an article matching '{title_query}'. Please try a different title or ask for 'articles about [topic]'."

    # --- Articles by a specific author ---
    author_articles_match = re.search(r'(?:articles|stories) (?:by|written by) ([a-zA-Z ]+)', msg)
    if not author_articles_match:
        author_articles_match = re.search(r'what articles are written by ([a-zA-Z ]+)', msg)
    if not author_articles_match:
        author_articles_match = re.search(r'articles by ([a-zA-Z ]+)', msg)

    if author_articles_match:
        author_name = author_articles_match.group(1).strip()
        articles = Article.objects.filter(
            status='published',
            author__name__icontains=author_name
        )[:10]
        if articles:
            lines = '\n'.join([f"- {a.title} by {a.author.name}" for a in articles])
            return f"Articles written by {author_name}:\n{lines}"
        else:
            return f"No articles found by an author matching '{author_name}'."

    # --- Articles with a specific tag ---
    tag_articles_match = re.search(r'(?:articles|stories) with tag ["\']([a-zA-Z ]+)["\']', msg)
    if not tag_articles_match:
        tag_articles_match = re.search(r'tag ["\']([a-zA-Z ]+)["\']', msg)
    if not tag_articles_match:
        tag_articles_match = re.search(r'articles with tag ([a-zA-Z ]+)', msg)

    if tag_articles_match:
        tag_name = tag_articles_match.group(1).strip()
        try:
            tag = Tag.objects.get(name__iexact=tag_name)
            articles = tag.articles.filter(status='published')[:10]
            if articles:
                lines = '\n'.join([f"- {a.title} by {a.author.name}" for a in articles])
                return f"Articles with tag '{tag.name}':\n{lines}"
            else:
                return f"No articles found with tag '{tag.name}'."
        except Tag.DoesNotExist:
            return f"Tag '{tag_name}' not found."

    # --- Search articles by topic ---
    if re.search(r'articles about|search|find|articles on', msg):
        query_match = re.search(r'(?:articles about|search|find|articles on)\s+([\w\s]+)', msg)
        if query_match:
            query = query_match.group(1).strip()
            return answer_with_rag(query)
        else:
            return "Please specify what you want to search for (e.g., 'articles about technology')."

    # --- User profile ---
    if re.search(r'author|profile|who is', msg):
        handle_match = re.search(r'@([a-zA-Z0-9_-]+)', msg)
        if handle_match:
            handle = handle_match.group(1)
            profile = utils.get_user_profile(handle)
            if profile:
                return f"Profile of {profile['name']} (@{handle}):\nBio: {profile['bio']}\nFollowers: {profile['followers']}\nFollowing: {profile['following']}\nArticles: {profile['articles']}"
            else:
                return f"User @{handle} not found."
        else:
            return "Please specify a user handle (e.g., @username)."

    # --- Tags list ---
    if re.search(r'tags|topics|categories', msg):
        tags = utils.get_all_tags()
        if tags:
            tag_names = ', '.join([t['name'] for t in tags])
            return f"Available tags: {tag_names}"
        return "No tags found."

    # --- Bookmarks ---
    if re.search(r'bookmarks|saved articles', msg):
        if user and user.is_authenticated:
            bookmarks = utils.get_user_bookmarks(user)
            if 'error' in bookmarks:
                return bookmarks['error']
            if bookmarks:
                lines = '\n'.join([f"- {b['title']} by {b['author']}" for b in bookmarks])
                return f"Your bookmarked articles:\n{lines}"
            else:
                return "You have no bookmarked articles."
        else:
            return "You need to be signed in to see your bookmarks. Please log in."

    # --- Website info (how to questions) ---
    if re.search(r'how do (i|you|we) (write|create|publish|edit|save|follow|unfollow|comment|clap|bookmark|draft|delete|search|sign|profile)', msg):
        info = utils.get_website_info()
        # Return a relevant part of the info
        if 'write' in msg or 'create article' in msg:
            return info['how_to'].get('write_article', 'Go to the Write page.')
        if 'save article' in msg or 'bookmark' in msg:
            return info['how_to'].get('save_article', 'Click the Save button on the article page.')
        if 'follow' in msg:
            return info['how_to'].get('follow_user', 'Go to the user profile and click Follow.')
        if 'edit profile' in msg:
            return info['how_to'].get('edit_profile', 'Go to your profile and click Edit profile.')
        if 'publish' in msg or 'draft' in msg:
            return info['how_to'].get('publish_draft', 'Go to drafts, click the draft, then click Publish.')
        if 'delete' in msg:
            return info['how_to'].get('delete_article', 'In your profile, find the article and click Delete.')
        if 'search' in msg:
            return info['how_to'].get('search', 'Use the search bar in the navigation.')
        if 'comment' in msg:
            return info['how_to'].get('comment', 'Scroll to the bottom of an article, type your response, and click Respond.')
        if 'clap' in msg:
            return info['how_to'].get('clap', 'Click the clap button on an article.')
        if 'sign' in msg:
            return info['how_to'].get('signup', 'Click "Get started" to sign up, or "Sign in" to log in.')
        if 'profile' in msg:
            return info['how_to'].get('edit_profile', 'Go to your profile and click Edit profile.')
        # Fallback: return general info
        return "Here is general information about the website:\n" + json.dumps(info, indent=2)

    return ("I'm sorry, I don't have an answer for that. You can ask me about:\n"
            "- Latest articles\n"
            "- Trending articles\n"
            "- Author of 'title'\n"
            "- Articles about [topic]\n"
            "- Tags\n"
            "- User profile @handle\n"
            "- Bookmarks (if signed in)\n"
            "- How many articles/tags/users there are\n"
            "- How to write, edit, save, follow, comment, clap, etc.")

def coerce_args(tool_name, args):
    if tool_name == 'get_article':
        if 'article_id' in args:
            try:
                args['article_id'] = int(args['article_id'])
            except (ValueError, TypeError):
                raise ValueError("article_id must be an integer.")
    if tool_name in ['search_articles', 'search_articles_semantic', 'search_users']:
        if 'limit' in args:
            try:
                args['limit'] = int(args['limit'])
            except (ValueError, TypeError):
                args['limit'] = 10
    if tool_name == 'get_trending_articles':
        if 'limit' in args:
            try:
                args['limit'] = int(args['limit'])
            except (ValueError, TypeError):
                args['limit'] = 5
    return args

class ChatbotView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'chatbot'

    def post(self, request):
        user = request.user
        data = request.data
        message = data.get('message', '').strip()
        history = data.get('history', [])

        if not message:
            return Response({'error': 'No message provided.'}, status=status.HTTP_400_BAD_REQUEST)

        if USE_MOCK or client is None:
            logger.info("Using MOCK response.")
            answer = get_mock_response(message, user)
            return Response({'answer': answer, 'function_called': 'mock'})

        try:
            anthropic_tools = []
            for tool in TOOLS:
                anthropic_tools.append({
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["input_schema"]
                })

            system_prompt = (
                "You are a helpful assistant for a Medium‑like blog website called 'Blog'. "
                "You MUST use the provided tools to retrieve real data from the database. "
                "DO NOT guess or make up answers. If a user asks for articles, authors, tags, bookmarks, etc., "
                "you MUST call the appropriate tool. Only after receiving the tool result, you can answer the user. "
                "For topic or open-ended questions, prefer 'search_articles_semantic' (vector/RAG search) over keyword search. "
                "If a user asks about something that requires authentication (like bookmarks), inform them politely. "
                "Additionally, you can answer questions about how the website works, its features, and how to use them. "
                "Use the 'get_website_info' tool to get a description of the website features and instructions on how to perform common tasks. "
                "ONLY answer questions that are related to this website — its articles, authors, tags, or how to use it. "
                "If the user asks something unrelated to the website (general knowledge, weather, sports, current events, coding help, etc.), "
                "do NOT answer it and do NOT call any tool. Instead reply with EXACTLY: 'Sorry, I can only answer questions about this website.' "
                "Keep your answers concise and helpful. Do not expose private information of other users."
            )

            messages = []
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": message})

            response = client.messages.create(
                model=model_name,
                system=system_prompt,
                messages=messages,
                tools=anthropic_tools,
                tool_choice={"type": "auto"},
                max_tokens=4096,
                temperature=0.7,
            )

            tool_use_block = None
            content_blocks = response.content
            for block in content_blocks:
                if block.type == "tool_use":
                    tool_use_block = block
                    break

            if tool_use_block:
                tool_name = tool_use_block.name
                tool_input = tool_use_block.input
                tool_id = tool_use_block.id

                try:
                    tool_input = coerce_args(tool_name, tool_input)
                except ValueError as e:
                    return Response({'answer': str(e), 'function_called': 'error'})

                func = TOOL_MAP.get(tool_name)
                if not func:
                    raise ValueError(f"Unknown tool: {tool_name}")

                if tool_name in ['get_user_bookmarks', 'get_user_comments']:
                    result = func(user)
                else:
                    result = func(**tool_input)

                assistant_message = {"role": "assistant", "content": content_blocks}
                messages.append(assistant_message)

                tool_result_message = {
                    "role": "user",
                    "content": [{"type": "tool_result", "tool_use_id": tool_id, "content": json.dumps(result)}]
                }
                messages.append(tool_result_message)

                final_response = client.messages.create(
                    model=model_name,
                    system=system_prompt,
                    messages=messages,
                    max_tokens=4096,
                    temperature=0.7,
                )
                final_answer = final_response.content[0].text
                return Response({'answer': final_answer, 'function_called': tool_name})
            else:
                answer = response.content[0].text
                return Response({'answer': answer, 'function_called': None})

        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            answer = get_mock_response(message, user)
            return Response({'answer': answer, 'function_called': 'mock-fallback'})