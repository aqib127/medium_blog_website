from django.db import models
from django.db.models import Max, Sum, Count, Q
from articles.models import Article, Tag
from users.models import User, Follow
from bookmarks.models import Bookmark
from reading_history.models import ReadingHistory
from django.contrib.auth import get_user_model

User = get_user_model()

# ------------------------------------------------------------------
# Tag queries – enhanced
# ------------------------------------------------------------------
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

# --- NEW: Tag-based sorted queries ---
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

# ------------------------------------------------------------------
# Article queries
# ------------------------------------------------------------------
def get_top_articles_by_claps(limit=5):
    articles = Article.objects.filter(status='published').order_by('-claps_count')[:limit]
    return [
        {
            'title': a.title,
            'author': a.author.name,
            'claps': a.claps_count,
            'comments': a.comments_count,
        }
        for a in articles
    ]

def get_top_articles_by_comments(limit=5):
    articles = Article.objects.filter(status='published').order_by('-comments_count')[:limit]
    return [
        {
            'title': a.title,
            'author': a.author.name,
            'claps': a.claps_count,
            'comments': a.comments_count,
        }
        for a in articles
    ]

def get_top_articles_by_views(limit=5):
    try:
        articles = Article.objects.filter(status='published').order_by('-view_count')[:limit]
        return [
            {
                'title': a.title,
                'author': a.author.name,
                'views': a.view_count,
            }
            for a in articles
        ]
    except AttributeError:
        return None

def get_most_bookmarked_articles(limit=5):
    articles = Article.objects.filter(status='published').annotate(
        bookmarks_count=models.Count('bookmarks')
    ).order_by('-bookmarks_count')[:limit]
    return [
        {
            'title': a.title,
            'author': a.author.name,
            'bookmarks': a.bookmarks_count,
        }
        for a in articles
    ]

def get_articles_by_author(author_name):
    articles = Article.objects.filter(
        status='published',
        author__name__icontains=author_name
    )[:10]
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
        {
            'title': a.title,
            'author': a.author.name,
            'claps': a.claps_count,
            'comments': a.comments_count,
        }
        for a in articles
    ]

def get_trending_articles(limit=5):
    articles = Article.objects.filter(status='published').order_by('-claps_count')[:limit]
    return [
        {
            'title': a.title,
            'author': a.author.name,
            'claps': a.claps_count,
        }
        for a in articles
    ]

def get_featured_article():
    a = Article.objects.filter(featured=True, status='published').first()
    if not a:
        return None
    return {
        'title': a.title,
        'author': a.author.name,
        'dek': a.dek,
    }

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
        {
            'title': a.title,
            'author': a.author.name,
            'claps': a.claps_count,
            'comments': a.comments_count,
        }
        for a in articles
    ]

def get_articles_with_min_comments(min_comments=10):
    articles = Article.objects.filter(status='published', comments_count__gte=min_comments)
    return [
        {
            'title': a.title,
            'author': a.author.name,
            'claps': a.claps_count,
            'comments': a.comments_count,
        }
        for a in articles
    ]

def get_articles_by_author_and_tag(author_name, tag_name):
    articles = Article.objects.filter(
        status='published',
        author__name__icontains=author_name,
        tags__name__iexact=tag_name
    ).distinct()[:10]
    return [
        {
            'title': a.title,
            'author': a.author.name,
            'claps': a.claps_count,
            'comments': a.comments_count,
        }
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
        {
            'title': a.title,
            'author': a.author.name,
            'published_at': a.published_at.isoformat() if a.published_at else None,
        }
        for a in articles
    ]

# ------------------------------------------------------------------
# Tag queries (basic)
# ------------------------------------------------------------------
def get_all_tags():
    tags = Tag.objects.all()
    return [{'name': t.name, 'slug': t.slug} for t in tags]

def get_tag_frequency():
    tags = Tag.objects.annotate(count=Count('articles')).order_by('-count')
    return [{'name': t.name, 'count': t.count} for t in tags]

def get_total_tags():
    return Tag.objects.count()

# ------------------------------------------------------------------
# User & following queries
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# Reading history
# ------------------------------------------------------------------
def get_reading_history(user):
    if not user or not user.is_authenticated:
        return None
    try:
        history = ReadingHistory.objects.filter(user=user).order_by('-viewed_at').select_related('article')[:20]
        return [
            {
                'article': h.article.title,
                'viewed_at': h.viewed_at.isoformat(),
            }
            for h in history
        ]
    except (AttributeError, NameError):
        return None

# ------------------------------------------------------------------
# Bookmark queries
# ------------------------------------------------------------------
def get_bookmarked_articles(user):
    if not user or not user.is_authenticated:
        return None
    bookmarks = Bookmark.objects.filter(user=user).select_related('article')
    return [
        {
            'title': b.article.title,
            'author': b.article.author.name,
            'bookmarked_at': b.created_at.isoformat(),
        }
        for b in bookmarks
    ]

def get_bookmarks_for_user_by_handle(handle, requesting_user):
    target_user = get_user_by_handle(handle)
    if not target_user:
        return None
    if not (requesting_user and (requesting_user == target_user or requesting_user.is_superuser)):
        return None
    return get_bookmarked_articles(target_user)

# ------------------------------------------------------------------
# Website info & features
# ------------------------------------------------------------------
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