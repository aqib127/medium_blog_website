from articles.models import Article, Tag
from users.models import User, Follow
from bookmarks.models import Bookmark
from comments.models import Comment
from django.db.models import Q

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
        a = Article.objects.filter(featured=True, status='published').first()
        if a:
            return {
                'id': a.id,
                'title': a.title,
                'author': a.author.name,
                'dek': a.dek,
            }
        return None
    except:
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

def get_website_info():
    """Return a comprehensive description of the website and its features."""
    return {
        "name": "Blog - A Medium-style Writing Platform",
        "description": "Blog is a platform for writers and readers to share long-form articles and ideas.",
        "features": {
            "authentication": "Users can sign up, sign in, and sign out. Authentication uses JWT tokens.",
            "profiles": "Each user has a profile with bio, avatar, and social links. Users can edit their profile.",
            "articles": "Users can write, edit, publish, and delete articles. Articles support rich text (Quill), tags, and a dek.",
            "drafts": "Articles can be saved as drafts before publishing.",
            "reading_list": "Users can bookmark articles to save them for later.",
            "claps": "Readers can clap for articles (like/unlike) - one clap per user per article.",
            "comments": "Users can comment on articles. Comments are shown below the article.",
            "following": "Users can follow other users. Followers count is displayed on profiles.",
            "tag_filtering": "Articles are tagged. Users can filter articles by clicking a tag.",
            "search": "Users can search articles by title, dek, or body content.",
            "chatbot": "This AI assistant can answer questions about the website and its features.",
            "notifications": "Users receive notifications for follows, comments, claps, etc. (if implemented)."
        },
        "how_to": {
            "write_article": "Go to the Write page (top navigation) and fill in the title, dek, content, and select a tag. Click 'Publish' to publish or 'Save draft' to save as draft.",
            "edit_article": "If you have published or drafted articles, you can edit them from your profile page or from the drafts page.",
            "save_article": "Click the Save button on an article to add it to your reading list.",
            "follow_user": "On a user's profile page, click the Follow button.",
            "edit_profile": "Go to your profile page and click 'Edit profile' or go to Settings.",
            "view_saved": "Click 'Saved' in the dropdown menu under your avatar.",
            "publish_draft": "Go to your drafts page, click the draft to open the editor, then click Publish.",
            "delete_article": "In your profile, under Stories or Drafts, find the article and click Delete.",
            "search": "Use the search bar in the navigation to search for articles by title, topic, or writer.",
            "bookmark": "Click the Save button on any article to bookmark it. Find saved articles under 'Saved' in the dropdown.",
            "clap": "Click the clap button (hands icon) on an article to show appreciation. You can only clap once per article.",
            "comment": "Scroll to the bottom of an article, type your response in the text area, and click Respond.",
            "signup": "Click 'Get started' on the homepage or go to the Sign Up page to create an account.",
            "signin": "Click 'Sign in' in the navigation to log in with your email and password."
        }
    }