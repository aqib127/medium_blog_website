from articles.models import Article, Tag
from users.models import User, Follow
from bookmarks.models import Bookmark
from comments.models import Comment
from django.db.models import Q
from django.shortcuts import get_object_or_404

def search_articles(query, limit=10):
    """Search articles by title, dek, body, or tag name."""
    if not query:
        return []
    q = Q(title__icontains=query) | Q(dek__icontains=query) | Q(body__icontains=query)
    tag_q = Q(tags__name__icontains=query)
    results = Article.objects.filter(q | tag_q, status='published').distinct()[:limit]
    return [
        {
            'id': a.id,
            'title': a.title,
            'dek': a.dek,
            'author': a.author.name,
            'tags': [t.name for t in a.tags.all()],
            'claps': a.claps_count,
            'comments': a.comments_count,
            'published_at': a.published_at.isoformat() if a.published_at else None,
        }
        for a in results
    ]

def get_article(article_id):
    """Get detailed information about a specific article."""
    try:
        a = Article.objects.get(id=article_id, status='published')
        return {
            'id': a.id,
            'title': a.title,
            'dek': a.dek,
            'body': a.body[:500] + ('...' if len(a.body) > 500 else ''),
            'author': a.author.name,
            'author_handle': a.author.handle,
            'tags': [t.name for t in a.tags.all()],
            'claps': a.claps_count,
            'comments': a.comments_count,
            'published_at': a.published_at.isoformat() if a.published_at else None,
        }
    except Article.DoesNotExist:
        return None

def get_user_profile(handle):
    """Get public profile of a user by handle."""
    try:
        u = User.objects.get(handle=handle)
        return {
            'name': u.name,
            'handle': u.handle,
            'bio': u.bio,
            'location': u.location,
            'followers': u.followers_count,
            'following': u.following_count,
            'articles': u.articles_count,
            'joined': u.date_joined.isoformat(),
        }
    except User.DoesNotExist:
        return None

def get_user_followers(handle):
    """Get list of followers for a user."""
    try:
        u = User.objects.get(handle=handle)
        followers = u.followers_set.all().select_related('follower')
        return [{'name': f.follower.name, 'handle': f.follower.handle} for f in followers]
    except User.DoesNotExist:
        return []

def get_user_following(handle):
    """Get list of users that a user is following."""
    try:
        u = User.objects.get(handle=handle)
        following = u.following_set.all().select_related('followed')
        return [{'name': f.followed.name, 'handle': f.followed.handle} for f in following]
    except User.DoesNotExist:
        return []

def get_user_bookmarks(user):
    """Get bookmarked articles for the authenticated user."""
    if not user or not user.is_authenticated:
        return {'error': 'Authentication required.'}
    bookmarks = Bookmark.objects.filter(user=user).select_related('article')
    return [
        {
            'id': b.article.id,
            'title': b.article.title,
            'author': b.article.author.name,
            'bookmarked_at': b.created_at.isoformat(),
        }
        for b in bookmarks
    ]

def get_user_comments(user):
    """Get comments made by the authenticated user."""
    if not user or not user.is_authenticated:
        return {'error': 'Authentication required.'}
    comments = Comment.objects.filter(author=user).select_related('article').order_by('-created_at')[:20]
    return [
        {
            'article': c.article.title,
            'text': c.text,
            'created_at': c.created_at.isoformat(),
        }
        for c in comments
    ]

def get_trending_articles(limit=5):
    """Get trending articles by claps."""
    articles = Article.objects.filter(status='published').order_by('-claps_count')[:limit]
    return [
        {
            'id': a.id,
            'title': a.title,
            'author': a.author.name,
            'claps': a.claps_count,
        }
        for a in articles
    ]

def get_featured_article():
    """Get the featured article."""
    try:
        a = Article.objects.get(featured=True, status='published')
        return {
            'id': a.id,
            'title': a.title,
            'author': a.author.name,
            'dek': a.dek,
        }
    except Article.DoesNotExist:
        return None

def get_articles_by_tag(tag_slug):
    """Get articles by tag slug."""
    try:
        tag = Tag.objects.get(slug=tag_slug)
        articles = tag.articles.filter(status='published')[:10]
        return [
            {
                'id': a.id,
                'title': a.title,
                'author': a.author.name,
                'published_at': a.published_at.isoformat() if a.published_at else None,
            }
            for a in articles
        ]
    except Tag.DoesNotExist:
        return []

def search_users(query, limit=10):
    """Search users by name or handle."""
    if not query:
        return []
    users = User.objects.filter(Q(name__icontains=query) | Q(handle__icontains=query))[:limit]
    return [{'name': u.name, 'handle': u.handle, 'bio': u.bio} for u in users]

def get_all_tags():
    """Get list of all tags."""
    tags = Tag.objects.all()
    return [{'name': t.name, 'slug': t.slug} for t in tags]