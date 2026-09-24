"""
rag_langchain/tools.py

Two categories of tools:

1. QUERY HELPERS (existing) — pure read functions used by LangChain chain.py
   e.g. get_top_articles_by_claps, get_user_profile, etc.

2. ACTION TOOLS (new) — function-calling tools that MUTATE state
   e.g. publish_article, like_article, follow_user
"""

from django.db import models
from django.db.models import Max, Sum, Count, Q
from articles.models import Article, Tag, Clap
from users.models import User, Follow
from bookmarks.models import Bookmark
from reading_history.models import ReadingHistory
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)
User = get_user_model()

# PART 1: EXISTING QUERY FUNCTIONS (KEEP ALL — DO NOT DELETE)

# Tag queries – enhanced

def get_tag_article_count():
    tags = Tag.objects.annotate(count=Count('articles')).order_by('-count')
    return [{'name': t.name, 'count': t.count} for t in tags]

def get_tag_total_claps():
    tags = Tag.objects.annotate(total_claps=Sum('articles__claps_count')).order_by('-total_claps')
    return [{'name': t.name, 'total_claps': t.total_claps or 0} for t in tags]

def get_tag_total_comments():
    tags = Tag.objects.annotate(total_comments=Sum('articles__comments_count')).order_by('-total_comments')
    return [{'name': t.name, 'total_comments': t.total_comments or 0} for t in tags]

def get_tag_total_views():
    try:
        tags = Tag.objects.annotate(total_views=Sum('articles__view_count')).order_by('-total_views')
        return [{'name': t.name, 'total_views': t.total_views or 0} for t in tags]
    except AttributeError:
        return None

def get_latest_article_per_tag():
    from django.db.models import Subquery, OuterRef
    latest_articles = Article.objects.filter(
        status='published',
        tags=OuterRef('pk')
    ).order_by('-published_at').values('id')[:1]

    tags = Tag.objects.annotate(
        latest_article_id=Subquery(latest_articles)
    ).filter(latest_article_id__isnull=False)

    result = []
    for tag in tags:
        article = Article.objects.get(id=tag.latest_article_id)
        result.append({
            'tag': tag.name,
            'title': article.title,
            'author': article.author.name,
            'published_at': article.published_at.isoformat() if article.published_at else None,
        })
    return result

def get_articles_by_tag_partial(query):
    words = query.split()
    if not words:
        return []
    q_filter = Q()
    for word in words:
        q_filter |= Q(tags__name__icontains=word)
    articles = Article.objects.filter(q_filter, status='published').distinct()[:20]
    return [
        {
            'title': a.title,
            'author': a.author.name,
            'tags': [t.name for t in a.tags.all()],
            'claps': a.claps_count,
            'comments': a.comments_count,
        }
        for a in articles
    ]

def get_articles_grouped_by_tag():
    tags = Tag.objects.all().prefetch_related('articles')
    result = {}
    for tag in tags:
        articles = tag.articles.filter(status='published')
        if articles.exists():
            result[tag.name] = [
                {
                    'title': a.title,
                    'author': a.author.name,
                    'claps': a.claps_count,
                    'comments': a.comments_count,
                }
                for a in articles[:10]
            ]
    return result

def get_articles_by_tag_sorted(tag_name, sort_by='-claps_count', limit=5):
    tag = Tag.objects.filter(name__iexact=tag_name).first()
    if not tag:
        return []
    articles = tag.articles.filter(status='published').order_by(sort_by)[:limit]
    return [
        {
            'title': a.title,
            'author': a.author.name,
            'claps': a.claps_count,
            'comments': a.comments_count,
            'published_at': a.published_at.isoformat() if a.published_at else None,
        }
        for a in articles
    ]

def get_articles_by_partial_tag_sorted(query, sort_by='-claps_count', limit=5):
    words = query.split()
    if not words:
        return []
    q_filter = Q()
    for word in words:
        q_filter |= Q(tags__name__icontains=word)
    articles = Article.objects.filter(q_filter, status='published').distinct().order_by(sort_by)[:limit]
    return [
        {
            'title': a.title,
            'author': a.author.name,
            'tags': [t.name for t in a.tags.all()],
            'claps': a.claps_count,
            'comments': a.comments_count,
        }
        for a in articles
    ]

# Article queries

def get_top_articles_by_claps(limit=5):
    articles = Article.objects.filter(status='published').order_by('-claps_count')[:limit]
    return [
        {'title': a.title, 'author': a.author.name, 'claps': a.claps_count, 'comments': a.comments_count}
        for a in articles
    ]

def get_top_articles_by_comments(limit=5):
    articles = Article.objects.filter(status='published').order_by('-comments_count')[:limit]
    return [
        {'title': a.title, 'author': a.author.name, 'claps': a.claps_count, 'comments': a.comments_count}
        for a in articles
    ]

def get_top_articles_by_views(limit=5):
    try:
        articles = Article.objects.filter(status='published').order_by('-view_count')[:limit]
        return [{'title': a.title, 'author': a.author.name, 'views': a.view_count} for a in articles]
    except AttributeError:
        return None

def get_most_bookmarked_articles(limit=5):
    articles = Article.objects.filter(status='published').annotate(
        bookmarks_count=models.Count('bookmarks')
    ).order_by('-bookmarks_count')[:limit]
    return [
        {'title': a.title, 'author': a.author.name, 'bookmarks': a.bookmarks_count}
        for a in articles
    ]

def get_articles_by_author(author_name):
    articles = Article.objects.filter(status='published', author__name__icontains=author_name)[:10]
    return [
        {
            'title': a.title,
            'author': a.author.name,
            'claps': a.claps_count,
            'comments': a.comments_count,
            'published_at': a.published_at.isoformat() if a.published_at else None,
        }
        for a in articles
    ]

def get_articles_by_tag(tag_name):
    tag = Tag.objects.filter(name__iexact=tag_name).first()
    if not tag:
        return []
    articles = tag.articles.filter(status='published')[:10]
    return [
        {'title': a.title, 'author': a.author.name, 'claps': a.claps_count, 'comments': a.comments_count}
        for a in articles
    ]

def get_trending_articles(limit=5):
    articles = Article.objects.filter(status='published').order_by('-claps_count')[:limit]
    return [{'title': a.title, 'author': a.author.name, 'claps': a.claps_count} for a in articles]

def get_featured_article():
    a = Article.objects.filter(featured=True, status='published').first()
    if not a:
        return None
    return {'title': a.title, 'author': a.author.name, 'dek': a.dek}

def get_article_details(article_id):
    try:
        a = Article.objects.get(id=article_id, status='published')
        return {
            'title': a.title,
            'author': a.author.name,
            'claps': a.claps_count,
            'comments': a.comments_count,
            'dek': a.dek,
            'body': a.body[:500] + '...' if len(a.body) > 500 else a.body,
        }
    except Article.DoesNotExist:
        return None

def get_articles_with_min_claps(min_claps=10):
    articles = Article.objects.filter(status='published', claps_count__gte=min_claps)
    return [
        {'title': a.title, 'author': a.author.name, 'claps': a.claps_count, 'comments': a.comments_count}
        for a in articles
    ]

def get_articles_with_min_comments(min_comments=10):
    articles = Article.objects.filter(status='published', comments_count__gte=min_comments)
    return [
        {'title': a.title, 'author': a.author.name, 'claps': a.claps_count, 'comments': a.comments_count}
        for a in articles
    ]

def get_articles_by_author_and_tag(author_name, tag_name):
    articles = Article.objects.filter(
        status='published',
        author__name__icontains=author_name,
        tags__name__iexact=tag_name
    ).distinct()[:10]
    return [
        {'title': a.title, 'author': a.author.name, 'claps': a.claps_count, 'comments': a.comments_count}
        for a in articles
    ]

def get_latest_article_per_author():
    latest_per_author = Article.objects.filter(status='published').values('author_id').annotate(
        latest_pub=Max('published_at')
    )
    article_ids = []
    for entry in latest_per_author:
        article = Article.objects.filter(
            author_id=entry['author_id'],
            published_at=entry['latest_pub']
        ).first()
        if article:
            article_ids.append(article.id)
    articles = Article.objects.filter(id__in=article_ids).select_related('author')
    return [
        {'title': a.title, 'author': a.author.name, 'published_at': a.published_at.isoformat() if a.published_at else None}
        for a in articles
    ]

# Tag queries (basic)

def get_all_tags():
    tags = Tag.objects.all()
    return [{'name': t.name, 'slug': t.slug} for t in tags]

def get_tag_frequency():
    tags = Tag.objects.annotate(count=Count('articles')).order_by('-count')
    return [{'name': t.name, 'count': t.count} for t in tags]

def get_total_tags():
    return Tag.objects.count()

# User & following queries

def get_total_users():
    return User.objects.count()

def get_user_by_handle(handle):
    try:
        return User.objects.get(handle=handle)
    except User.DoesNotExist:
        return None

def get_user_profile(handle):
    try:
        u = User.objects.get(handle=handle)
        return {
            'name': u.name,
            'handle': u.handle,
            'bio': u.bio,
            'followers': u.followers_count,
            'following': u.following_count,
            'articles': u.articles_count,
        }
    except User.DoesNotExist:
        return None

def get_user_followers(handle):
    try:
        u = User.objects.get(handle=handle)
        followers = u.followers_set.all().select_related('follower')
        return [{'name': f.follower.name, 'handle': f.follower.handle} for f in followers]
    except User.DoesNotExist:
        return []

def get_user_following(handle):
    try:
        u = User.objects.get(handle=handle)
        following = u.following_set.all().select_related('followed')
        return [{'name': f.followed.name, 'handle': f.followed.handle} for f in following]
    except User.DoesNotExist:
        return []

def does_user_follow(target_handle, current_user):
    if not current_user or not current_user.is_authenticated:
        return None
    try:
        target = User.objects.get(handle=target_handle)
        return Follow.objects.filter(follower=current_user, followed=target).exists()
    except User.DoesNotExist:
        return False

def get_follow_count():
    return Follow.objects.count()


# Reading history

def get_reading_history(user):
    if not user or not user.is_authenticated:
        return None
    try:
        history = ReadingHistory.objects.filter(user=user).order_by('-viewed_at').select_related('article')[:20]
        return [{'article': h.article.title, 'viewed_at': h.viewed_at.isoformat()} for h in history]
    except (AttributeError, NameError):
        return None


# Bookmark queries

def get_bookmarked_articles(user):
    if not user or not user.is_authenticated:
        return None
    bookmarks = Bookmark.objects.filter(user=user).select_related('article')
    return [
        {'title': b.article.title, 'author': b.article.author.name, 'bookmarked_at': b.created_at.isoformat()}
        for b in bookmarks
    ]

def get_bookmarks_for_user_by_handle(handle, requesting_user):
    target_user = get_user_by_handle(handle)
    if not target_user:
        return None
    if not (requesting_user and (requesting_user == target_user or requesting_user.is_superuser)):
        return None
    return get_bookmarked_articles(target_user)

# Website info & features

def get_website_info():
    return {
        'name': 'Blog - A Medium-style Writing Platform',
        'total_users': get_total_users(),
        'total_articles': Article.objects.filter(status='published').count(),
        'total_tags': Tag.objects.count(),
    }

def get_website_features():
    return [
        "Read and write articles",
        "Comment on articles",
        "Clap (like) articles",
        "Bookmark articles to read later",
        "Follow other users",
        "Edit your profile",
        "Search for articles and users",
        "Filter articles by tags",
        "View your reading history",
        "Manage your drafts",
        "Get notifications for interactions",
    ]

# PART 2: NEW ACTION TOOLS (function calling)

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "publish_article",
            "description": "Publish a new blog article for the currently logged-in user. Use when user says 'publish', 'post', 'create an article'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Article title (max 300 chars)"},
                    "body": {"type": "string", "description": "Full article body in markdown/text"},
                    "dek": {"type": "string", "description": "Optional short subtitle/description"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of tag names (e.g. ['AI', 'Python'])"
                    }
                },
                "required": ["title", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clap_article",
            "description": "Clap (like) an article by its ID. Use when user says 'clap for article 5', 'like this post', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "article_id": {"type": "integer", "description": "Article ID to clap"}
                },
                "required": ["article_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "unclap_article",
            "description": "Remove a clap from an article.",
            "parameters": {
                "type": "object",
                "properties": {
                    "article_id": {"type": "integer"}
                },
                "required": ["article_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "follow_user",
            "description": "Follow another user by their handle. Use when user says 'follow @john' or 'follow john'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "handle": {"type": "string", "description": "The handle/username to follow"}
                },
                "required": ["handle"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "unfollow_user",
            "description": "Unfollow a user by handle.",
            "parameters": {
                "type": "object",
                "properties": {
                    "handle": {"type": "string"}
                },
                "required": ["handle"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "bookmark_article",
            "description": "Bookmark/save an article for later reading.",
            "parameters": {
                "type": "object",
                "properties": {
                    "article_id": {"type": "integer"}
                },
                "required": ["article_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_articles",
            "description": "Search articles by keyword. Returns matching articles with IDs, titles, and authors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_following",
            "description": "Get the list of users that the currently logged-in user is following. Use when user asks 'show my following', 'who am I following', 'list my following'.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_trending_articles",
            "description": "Get the most popular/trending articles based on claps. Use when user asks 'show trending', 'what's popular', 'top articles'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 5}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_bookmarks",
            "description": "Get the list of articles bookmarked by the currently logged-in user. Use when user asks 'show my bookmarks', 'my saved articles'.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
]


def _tool_publish_article(user, title, body, dek="", tags=None):
    if not user or not user.is_authenticated:
        return {"error": "You must be logged in to publish articles."}

    # Generate unique slug — but Article model has NO slug field!
    # So we skip slug entirely.

    try:
        article = Article.objects.create(
            author=user,
            title=title[:300],
            dek=dek or "",
            body=body,
            status=Article.Status.PUBLISHED,
            published_at=timezone.now(),
        )
    except Exception as e:
        logger.exception("Article create failed")
        return {"error": f"Failed to publish: {e}"}

    # Add tags via ArticleTag through-model
    if tags:
        try:
            from articles.models import ArticleTag
            for tag_name in tags[:10]:
                tag_name = tag_name.strip()[:50]
                if not tag_name:
                    continue
                tag_slug = slugify(tag_name)
                tag, _ = Tag.objects.get_or_create(
                    slug=tag_slug,
                    defaults={"name": tag_name}
                )
                ArticleTag.objects.get_or_create(article=article, tag=tag)
        except Exception as e:
            logger.warning(f"Tag add failed: {e}")

    # Update user's article count
    try:
        user.articles_count = user.articles.count()
        user.save(update_fields=["articles_count"])
    except Exception:
        pass

    # ✅ Invalidate trending cache
    cache.delete("trending_articles_5")
    cache.delete("trending_articles_10")

    return {
        "success": True,
        "article_id": article.id,
        "title": article.title,
        "url": f"/article/{article.id}",
        "message": f"Article '{article.title}' published successfully (ID: {article.id})."
    }


def _tool_clap_article(user, article_id):
    if not user or not user.is_authenticated:
        return {"error": "Login required."}

    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        return {"error": f"Article with id {article_id} not found."}

    clap, created = Clap.objects.get_or_create(user=user, article=article)

    if created:
        # Update denormalized counter
        Article.objects.filter(id=article.id).update(
            claps_count=models.F('claps_count') + 1
        )
        article.refresh_from_db()
        # ✅ Invalidate trending cache (claps changed)
        cache.delete("trending_articles_5")
        cache.delete("trending_articles_10")

    return {
        "success": True,
        "clapped": True,
        "already_clapped": not created,
        "article_id": article.id,
        "title": article.title,
        "claps_count": article.claps_count,
        "message": f"{'Already clapped' if not created else 'Clapped'} '{article.title}'."
    }


def _tool_unclap_article(user, article_id):
    if not user or not user.is_authenticated:
        return {"error": "Login required."}

    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        return {"error": f"Article {article_id} not found."}

    deleted, _ = Clap.objects.filter(user=user, article=article).delete()

    if deleted:
        Article.objects.filter(id=article.id).update(
            claps_count=models.functions.Greatest(
                models.F('claps_count') - 1, 0
            )
        )
        article.refresh_from_db()
        # ✅ Invalidate trending cache
        cache.delete("trending_articles_5")
        cache.delete("trending_articles_10")

    return {
        "success": True,
        "clapped": False,
        "article_id": article.id,
        "claps_count": article.claps_count,
        "message": f"Removed clap from '{article.title}'." if deleted else "You hadn't clapped this."
    }


def _tool_follow_user(user, handle):
    if not user or not user.is_authenticated:
        return {"error": "Login required."}

    handle = handle.lstrip("@").strip()
    if handle.lower() == (user.handle or "").lower():
        return {"error": "You can't follow yourself."}

    try:
        target = User.objects.get(handle__iexact=handle)
    except User.DoesNotExist:
        return {"error": f"User '@{handle}' not found."}

    follow, created = Follow.objects.get_or_create(follower=user, followed=target)

    if created:
        # Update denormalized counters
        User.objects.filter(id=user.id).update(following_count=models.F('following_count') + 1)
        User.objects.filter(id=target.id).update(followers_count=models.F('followers_count') + 1)

    return {
        "success": True,
        "following": True,
        "already_following": not created,
        "handle": target.handle,
        "name": target.name,
        "message": f"{'Already following' if not created else 'Now following'} @{target.handle}."
    }


def _tool_unfollow_user(user, handle):
    if not user or not user.is_authenticated:
        return {"error": "Login required."}

    handle = handle.lstrip("@").strip()
    try:
        target = User.objects.get(handle__iexact=handle)
    except User.DoesNotExist:
        return {"error": f"User '@{handle}' not found."}

    deleted, _ = Follow.objects.filter(follower=user, followed=target).delete()

    if deleted:
        User.objects.filter(id=user.id).update(following_count=models.functions.Greatest(
            models.F('following_count') - 1, 0
        ))
        User.objects.filter(id=target.id).update(followers_count=models.functions.Greatest(
            models.F('followers_count') - 1, 0
        ))

    return {
        "success": True,
        "following": False,
        "handle": target.handle,
        "message": f"Unfollowed @{target.handle}." if deleted else "You weren't following them."
    }


def _tool_bookmark_article(user, article_id):
    if not user or not user.is_authenticated:
        return {"error": "Login required."}

    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        return {"error": f"Article {article_id} not found."}

    bm, created = Bookmark.objects.get_or_create(user=user, article=article)
    return {
        "success": True,
        "bookmarked": True,
        "already_bookmarked": not created,
        "article_id": article.id,
        "title": article.title,
        "message": f"{'Already bookmarked' if not created else 'Bookmarked'} '{article.title}'."
    }


def _tool_search_articles(user, query, limit=5):
    qs = Article.objects.filter(status='published').filter(
        Q(title__icontains=query) | Q(body__icontains=query) | Q(dek__icontains=query)
    ).order_by('-published_at')[:int(limit)]

    results = [
        {
            "id": a.id,
            "title": a.title,
            "author": a.author.name,
            "author_handle": a.author.handle,
            "claps": a.claps_count,
        }
        for a in qs
    ]
    return {
        "success": True,
        "count": len(results),
        "results": results,
        "message": f"Found {len(results)} article(s)."
    }

# TOOL DISPATCHER



def _tool_get_my_following(user):
    """Get list of users the current user is following."""
    if not user or not user.is_authenticated:
        return {"error": "Login required."}

    follows = Follow.objects.filter(follower=user).select_related('followed')[:20]
    results = [
        {
            "handle": f.followed.handle,
            "name": f.followed.name,
            "bio": (f.followed.bio or "")[:100],
        }
        for f in follows
    ]

    return {
        "success": True,
        "count": len(results),
        "results": results,
        "message": f"You are following {len(results)} user(s)."
    }


def _tool_get_trending_articles(user, limit=5):
    """Get trending articles by claps."""
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        limit = 5

    # ✅ Try cache first
    cache_key = f"trending_articles_{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info(f"Cache HIT: {cache_key}")
        return cached

    logger.info(f"Cache MISS: {cache_key}")
    articles = Article.objects.filter(status='published').order_by('-claps_count')[:limit]
    results = [
        {
            "id": a.id,
            "title": a.title,
            "author": a.author.name,
            "author_handle": a.author.handle,
            "claps": a.claps_count,
            "comments": a.comments_count,
        }
        for a in articles
    ]

    result = {
        "success": True,
        "count": len(results),
        "results": results,
        "message": f"Found {len(results)} trending article(s)."
    }

    cache.set(cache_key, result, 300)
    return result


def _tool_get_my_bookmarks(user):
    """Get list of articles bookmarked by current user."""
    if not user or not user.is_authenticated:
        return {"error": "Login required."}

    bookmarks = Bookmark.objects.filter(user=user).select_related(
        'article', 'article__author'
    ).order_by('-created_at')[:20]

    results = [
        {
            "id": b.article.id,
            "title": b.article.title,
            "author": b.article.author.name,
            "author_handle": b.article.author.handle,
            "bookmarked_at": b.created_at.isoformat(),
        }
        for b in bookmarks
    ]

    return {
        "success": True,
        "count": len(results),
        "results": results,
        "message": f"You have {len(results)} bookmark(s)."
    }


TOOL_REGISTRY = {
    "publish_article": _tool_publish_article,
    "clap_article": _tool_clap_article,
    "unclap_article": _tool_unclap_article,
    "follow_user": _tool_follow_user,
    "unfollow_user": _tool_unfollow_user,
    "bookmark_article": _tool_bookmark_article,
    "search_articles": _tool_search_articles,
    "get_my_following": _tool_get_my_following,
    "get_trending_articles": _tool_get_trending_articles,
    "get_my_bookmarks": _tool_get_my_bookmarks,
}


def execute_tool(tool_name: str, args: dict, user):
    """Execute a tool by name. Returns dict result."""
    fn = TOOL_REGISTRY.get(tool_name)
    if not fn:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        clean_args = {}
        for k, v in (args or {}).items():
            if isinstance(v, str) and k.endswith("_id"):
                try:
                    v = int(v)
                except ValueError:
                    return {"error": f"Invalid {k}: must be integer."}
            clean_args[k] = v

        return fn(user=user, **clean_args)
    except TypeError as e:
        logger.exception(f"Tool arg mismatch: {tool_name}")
        return {"error": f"Bad arguments for {tool_name}: {e}"}
    except Exception as e:
        logger.exception(f"Tool execution failed: {tool_name}")
        return {"error": f"Action failed: {str(e)}"}