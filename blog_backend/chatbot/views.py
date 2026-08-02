import json
import logging
import re
from django.conf import settings
from django.db.models import Q, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from openai import OpenAI
from . import utils
from articles.models import Article, Tag
from users.models import User

logger = logging.getLogger(__name__)

# Read settings
OPENAI_API_KEY = getattr(settings, 'OPENAI_API_KEY', '')
USE_MOCK = getattr(settings, 'USE_MOCK_CHATBOT', False) or not OPENAI_API_KEY

# Initialize OpenAI client only if key is present and mock is not forced
client = None
if OPENAI_API_KEY and not USE_MOCK:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        USE_MOCK = True  # fallback to mock on error

if USE_MOCK:
    logger.warning("Chatbot running in MOCK mode. No OpenAI API calls will be made.")


def get_mock_response(message, user=None):
    """Enhanced mock response logic."""
    msg = message.lower().strip()

    # 1. Count queries
    if re.search(r'how many articles|number of articles|article count', msg):
        count = Article.objects.filter(status='published').count()
        return f"There are {count} published articles on this site."

    if re.search(r'how many tags|number of tags|tag count', msg):
        count = Tag.objects.count()
        return f"There are {count} tags available."

    if re.search(r'how many users|number of users|user count', msg):
        count = User.objects.count()
        return f"There are {count} registered users."

    # 2. "Any more" / "more articles" / "show more"
    if re.search(r'(any more|more articles|show more|list more|additional)', msg):
        articles = Article.objects.filter(status='published').order_by('-published_at')[5:10]
        if articles:
            lines = '\n'.join([f"- {a.title} by {a.author.name}" for a in articles])
            return f"Here are more articles (next 5):\n{lines}\n\nTo see different ones, ask for 'articles about [topic]' or 'latest articles' again."
        else:
            return "I've shown you all available articles. Try asking about a specific topic."

    # 3. Trending articles
    if re.search(r'trending|popular|most claps', msg):
        articles = utils.get_trending_articles(limit=5)
        if articles:
            lines = '\n'.join([f"- {a['title']} by {a['author']} ({a['claps']} claps)" for a in articles])
            return f"Here are the current trending articles:\n{lines}"
        return "No trending articles found at the moment."

    # 4. Featured article
    if re.search(r'featured|highlight', msg):
        art = utils.get_featured_article()
        if art:
            return f"The featured article is '{art['title']}' by {art['author']}. Summary: {art['dek']}"
        return "No featured article is currently available."

    # 5. Latest articles
    if re.search(r'latest|newest|recent', msg):
        articles = Article.objects.filter(status='published').order_by('-published_at')[:5]
        if articles:
            lines = '\n'.join([f"- {a.title} by {a.author.name}" for a in articles])
            return f"Here are the latest articles:\n{lines}"
        return "No published articles found."

    # 6. Author of a specific article (improved)
    author_match = re.search(r"author of ['\"](.+?)['\"]", msg)
    if not author_match:
        author_match = re.search(r"who (?:is|wrote) ['\"](.+?)['\"]", msg)
    if not author_match:
        author_match = re.search(r"author of\s+(.+)", msg)
    if not author_match:
        author_match = re.search(r"who (?:is|wrote)\s+(.+)", msg)

    if author_match:
        title_query = author_match.group(1).strip()
        title_query = title_query.strip('"\'')
        if title_query:
            # Search by title (case‑insensitive, partial)
            article = Article.objects.filter(
                Q(status='published') & Q(title__icontains=title_query)
            ).first()
            if article:
                return f"The article '{article.title}' was written by {article.author.name}."
            # If not found, search in dek and body
            article = Article.objects.filter(
                Q(status='published') &
                (Q(dek__icontains=title_query) | Q(body__icontains=title_query))
            ).first()
            if article:
                return f"The article '{article.title}' (contains '{title_query}' in its content) was written by {article.author.name}."
            # Try exact match (case‑insensitive)
            article = Article.objects.filter(
                Q(status='published') & Q(title__iexact=title_query)
            ).first()
            if article:
                return f"The article '{article.title}' was written by {article.author.name}."
            # Remove common leading words and try again
            cleaned = re.sub(r'^(the|a|an)\s+', '', title_query, flags=re.I)
            if cleaned and cleaned != title_query:
                article = Article.objects.filter(
                    Q(status='published') & Q(title__icontains=cleaned)
                ).first()
                if article:
                    return f"The article '{article.title}' was written by {article.author.name}."
            return f"Sorry, I couldn't find an article matching '{title_query}'. Please try a different title or ask for 'articles about [topic]'."

    # 7. Search articles by topic
    if re.search(r'articles about|search|find|articles on', msg):
        query_match = re.search(r'(?:articles about|search|find|articles on)\s+([\w\s]+)', msg)
        if query_match:
            query = query_match.group(1).strip()
            results = utils.search_articles(query, limit=5)
            if results:
                lines = '\n'.join([f"- {a['title']} by {a['author']}" for a in results])
                return f"Articles matching '{query}':\n{lines}"
            else:
                return f"No articles found matching '{query}'. Try a different topic."
        else:
            return "Please specify what you want to search for (e.g., 'articles about technology')."

    # 8. Author / user profile
    if re.search(r'author|profile|who is|about', msg):
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

    # 9. Tags
    if re.search(r'tags|topics|categories', msg):
        tags = utils.get_all_tags()
        if tags:
            tag_names = ', '.join([t['name'] for t in tags])
            return f"Available tags: {tag_names}"
        return "No tags found."

    # 10. Bookmarks (requires authentication)
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

    # 11. Fallback with suggestions
    return ("I'm sorry, I don't have an answer for that. You can ask me about:\n"
            "- Latest articles\n"
            "- Trending articles\n"
            "- Author of 'title'\n"
            "- Articles about [topic]\n"
            "- Tags\n"
            "- User profile @handle\n"
            "- Bookmarks (if signed in)\n"
            "- How many articles/tags/users there are")


# --------------------------------------------------------------------
# OpenAI Function Definitions (used when not in mock mode)
# --------------------------------------------------------------------
SYSTEM_PROMPT = """You are a helpful assistant for a Medium‑like blog website. You can answer questions about articles, authors, tags, bookmarks, comments, and other site content.

You have access to the following functions:
- search_articles(query): Search for articles by title, dek, body, or tag.
- get_article(article_id): Get detailed info about a specific article.
- get_user_profile(handle): Get public profile of a user.
- get_user_followers(handle): List followers of a user.
- get_user_following(handle): List users followed by a user.
- get_user_bookmarks(): Get the current user's bookmarked articles (requires authentication).
- get_user_comments(): Get the current user's comments (requires authentication).
- get_trending_articles(limit=5): Get trending articles by claps.
- get_featured_article(): Get the featured article.
- get_articles_by_tag(tag_slug): Get articles by a specific tag.
- search_users(query): Search users by name or handle.
- get_all_tags(): Get list of all tags.

Always call a function when you need fresh data. If the user asks about something that requires authentication, politely inform them that they need to be signed in.
"""

FUNCTION_MAP = {
    'search_articles': utils.search_articles,
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
}

FUNCTIONS = [
    {
        "name": "search_articles",
        "description": "Search for articles matching a query (by title, dek, body, or tag).",
        "parameters": {
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
        "description": "Get detailed information about a specific article by its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "article_id": {"type": "integer", "description": "ID of the article"}
            },
            "required": ["article_id"]
        }
    },
    {
        "name": "get_user_profile",
        "description": "Get public profile of a user by handle.",
        "parameters": {
            "type": "object",
            "properties": {
                "handle": {"type": "string", "description": "User's handle (username)"}
            },
            "required": ["handle"]
        }
    },
    {
        "name": "get_user_followers",
        "description": "List followers of a user.",
        "parameters": {
            "type": "object",
            "properties": {
                "handle": {"type": "string", "description": "User's handle"}
            },
            "required": ["handle"]
        }
    },
    {
        "name": "get_user_following",
        "description": "List users followed by a user.",
        "parameters": {
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
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "get_user_comments",
        "description": "Get the current user's comments. Requires authentication.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "get_trending_articles",
        "description": "Get trending articles by claps.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of articles", "default": 5}
            }
        }
    },
    {
        "name": "get_featured_article",
        "description": "Get the featured article.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "get_articles_by_tag",
        "description": "Get articles by a specific tag slug.",
        "parameters": {
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
        "parameters": {
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
        "parameters": {"type": "object", "properties": {}}
    }
]


# --------------------------------------------------------------------
# Main View
# --------------------------------------------------------------------
class ChatbotView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = request.user if request.user.is_authenticated else None
        data = request.data
        message = data.get('message', '').strip()
        history = data.get('history', [])

        if not message:
            return Response({'error': 'No message provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # Use mock if enabled
        if USE_MOCK:
            answer = get_mock_response(message, user)
            return Response({'answer': answer, 'function_called': 'mock'})

        # Real OpenAI path
        if client is None:
            return Response({
                'error': 'Chatbot is currently disabled. Please try again later.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": message}
        ]

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                functions=FUNCTIONS,
                function_call="auto",
                temperature=0.7,
            )

            response_message = response.choices[0].message

            if response_message.function_call:
                function_name = response_message.function_call.name
                arguments = json.loads(response_message.function_call.arguments)

                func = FUNCTION_MAP.get(function_name)
                if not func:
                    raise ValueError(f"Unknown function: {function_name}")

                if function_name in ['get_user_bookmarks', 'get_user_comments']:
                    result = func(user)
                else:
                    result = func(**arguments)

                messages.append(response_message)
                messages.append({
                    "role": "function",
                    "name": function_name,
                    "content": json.dumps(result),
                })

                second_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                )

                final_answer = second_response.choices[0].message.content
                return Response({'answer': final_answer, 'function_called': function_name})
            else:
                return Response({'answer': response_message.content, 'function_called': None})

        except Exception as e:
            logger.error(f"Chatbot error: {str(e)}")
            error_msg = str(e)
            if 'api_key' in error_msg.lower() or 'auth' in error_msg.lower():
                return Response({'error': 'Invalid OpenAI API key. Please check your configuration.'},
                                status=status.HTTP_401_UNAUTHORIZED)
            return Response({'error': 'An error occurred while processing your request.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)