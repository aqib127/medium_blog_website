"""
Django management command to populate the database with realistic sample data.
Run with: python manage.py populate_db
"""

import random
import uuid
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.db import transaction
from faker import Faker

# Import models
from users.models import User, Follow
from articles.models import Tag, Article, ArticleTag, ArticleImage
from comments.models import Comment
from bookmarks.models import Bookmark
from notifications.models import Notification
from reading_history.models import ReadingHistory
from reports.models import Report

fake = Faker()

class Command(BaseCommand):
    help = 'Populate the database with realistic sample data'

    # Sample topics for tags
    TOPICS = [
        ('Technology', 'tech'),
        ('Science', 'science'),
        ('Culture', 'culture'),
        ('Food', 'food'),
        ('Travel', 'travel'),
        ('Health', 'health'),
        ('Business', 'business'),
        ('Design', 'design'),
        ('Programming', 'programming'),
        ('Psychology', 'psychology'),
        ('History', 'history'),
        ('Philosophy', 'philosophy'),
        ('Art', 'art'),
        ('Music', 'music'),
        ('Literature', 'literature'),
    ]

    # Realistic user names and bios (to avoid purely random)
    FIRST_NAMES = [
        'Emma', 'Liam', 'Olivia', 'Noah', 'Ava', 'James', 'Sophia', 'Oliver',
        'Mia', 'Elijah', 'Charlotte', 'Lucas', 'Harper', 'Mason', 'Evelyn', 'Logan',
        'Amelia', 'Alexander', 'Abigail', 'Ethan', 'Ella', 'Jacob', 'Emily', 'Michael',
        'Scarlett', 'Benjamin', 'Victoria', 'Daniel', 'Aria', 'Matthew', 'Grace', 'David',
        'Chloe', 'Jackson', 'Luna', 'Sebastian', 'Layla', 'Carter', 'Zoe', 'Jayden',
        'Riley', 'Owen', 'Avery', 'Gabriel', 'Hazel', 'Julian', 'Lily', 'Wyatt',
        'Aubrey', 'Hunter', 'Addison', 'Levi', 'Stella', 'Isaiah', 'Nora', 'Eli',
        'Eleanor', 'Mila', 'Hudson', 'Aurora', 'Caleb', 'Leah', 'Connor', 'Sadie',
        'Adrian', 'Paisley', 'Nathan', 'Audrey', 'Ezekiel', 'Claire', 'Tristan', 'Bella',
        'Dominic', 'Skylar', 'Austin', 'Lucy', 'Colton', 'Ellie', 'Jose', 'Camila',
        'Mateo', 'Sofia', 'Xavier', 'Maya', 'Adam', 'Natalie', 'Alex', 'Julia',
        'Landon', 'Elena', 'Carson', 'Allison', 'Sawyer', 'Katherine', 'Emmett', 'Kinsley',
        'Jaxon', 'Lila', 'Beau', 'Naomi', 'Kai', 'Eloise', 'Theo', 'Ariana'
    ]

    LAST_NAMES = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
        'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas',
        'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White',
        'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
        'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill',
        'Flores', 'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell',
        'Mitchell', 'Carter', 'Roberts', 'Turner', 'Phillips', 'Evans', 'Collins',
        'Edwards', 'Stewart', 'Morris', 'Murphy', 'Cook', 'Rogers', 'Morgan',
        'Peterson', 'Cooper', 'Reed', 'Bailey', 'Bell', 'Howard', 'Ward', 'Cox',
        'Diaz', 'Richardson', 'Wood', 'Watson', 'Brooks', 'Bennett', 'Gray', 'James',
        'Reyes', 'Cruz', 'Hughes', 'Price', 'Myers', 'Long', 'Foster', 'Sanders',
        'Ross', 'Powell', 'Sullivan', 'Russell', 'Ortiz', 'Jenkins', 'Perry', 'Butler',
        'Barnes', 'Fisher', 'Henderson', 'Coleman', 'Simmons', 'Patterson', 'Jordan',
        'Reynolds', 'Hamilton', 'Graham', 'Kim', 'Gonzalez', 'Alexander', 'Ramsey'
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=120,
            help='Number of users to create (default: 120)'
        )
        parser.add_argument(
            '--articles',
            type=int,
            default=300,
            help='Number of articles to create (default: 300)'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Delete existing data before populating'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write('Cleaning existing data...')
            Report.objects.all().delete()
            ReadingHistory.objects.all().delete()
            Notification.objects.all().delete()
            Bookmark.objects.all().delete()
            Comment.objects.all().delete()
            ArticleTag.objects.all().delete()
            ArticleImage.objects.all().delete()
            Article.objects.all().delete()
            Tag.objects.all().delete()
            Follow.objects.all().delete()
            User.objects.all().delete()
            self.stdout.write('Data cleaned.')

        self.stdout.write('Creating sample data...')

        # 1. Create Tags – use 'name' as the lookup to avoid duplicate key errors
        self.stdout.write('Creating tags...')
        tags = []
        for name, slug in self.TOPICS:
            tag, created = Tag.objects.get_or_create(
                name=name,  # Use name as the unique identifier
                defaults={
                    'slug': slug,
                    'description': fake.sentence(nb_words=6)
                }
            )
            tags.append(tag)
        self.stdout.write(f'Created/retrieved {len(tags)} tags.')

        # 2. Create Users
        num_users = options['users']
        self.stdout.write(f'Creating {num_users} users...')
        users = []
        for i in range(num_users):
            first = random.choice(self.FIRST_NAMES)
            last = random.choice(self.LAST_NAMES)
            name = f"{first} {last}"
            handle = f"{first.lower()}.{last.lower()}"[:20] + f"_{i}" if i > 0 else f"{first.lower()}.{last.lower()}"[:20]
            while User.objects.filter(handle=handle).exists():
                handle += str(random.randint(1, 999))
            email = f"{handle}@example.com"
            bio = fake.text(max_nb_chars=160) if random.random() > 0.3 else ''
            location = f"{fake.city()}, {fake.country()}" if random.random() > 0.5 else ''
            twitter = f"@{handle}" if random.random() > 0.5 else ''
            github = handle if random.random() > 0.5 else ''
            website = fake.url() if random.random() > 0.5 else ''
            avatar_color = random.choice(['#1F4E4A', '#B8862E', '#D1495B', '#57524C', '#6B4226', '#2E6B7A', '#8B5A2B', '#4A6B8A', '#6B4A7A'])
            user = User.objects.create(
                email=email,
                name=name,
                handle=handle,
                bio=bio,
                location=location,
                twitter=twitter,
                github=github,
                website=website,
                avatar_color=avatar_color,
                password=make_password('rootroot'),
                is_active=True,
                date_joined=timezone.now() - timedelta(days=random.randint(1, 365*3))
            )
            users.append(user)

        self.stdout.write(f'Created {len(users)} users.')

        # 3. Create Follows
        self.stdout.write('Creating follows...')
        follow_count = 0
        for user in users:
            num_to_follow = random.randint(5, min(30, len(users)//2))
            potential = random.sample(users, min(num_to_follow, len(users)-1))
            for target in potential:
                if target == user:
                    continue
                if not Follow.objects.filter(follower=user, followed=target).exists():
                    Follow.objects.create(follower=user, followed=target)
                    follow_count += 1
        self.stdout.write(f'Created {follow_count} follows.')

        # 4. Create Articles
        num_articles = options['articles']
        self.stdout.write(f'Creating {num_articles} articles...')
        articles = []
        for user in users:
            num = random.randint(0, 3)
            for _ in range(num):
                if len(articles) >= num_articles:
                    break
                article_tags = random.sample(tags, k=random.randint(1, 3))
                title = fake.sentence(nb_words=random.randint(3, 8))[:-1]
                dek = fake.text(max_nb_chars=120) if random.random() > 0.3 else ''
                body = '\n\n'.join(fake.paragraphs(nb=random.randint(5, 15)))
                status = random.choice(['published', 'published', 'draft', 'archived'])
                featured = random.random() < 0.05
                cover_color = random.choice(['#1F4E4A', '#B8862E', '#D1495B', '#57524C', '#6B4226', '#2E6B7A', '#8B5A2B', '#4A6B8A', '#6B4A7A'])
                folio = f"{random.randint(1, 999):03d}"
                published_at = None
                if status == 'published':
                    published_at = timezone.now() - timedelta(days=random.randint(1, 180))
                elif status == 'archived':
                    published_at = timezone.now() - timedelta(days=random.randint(181, 365))
                scheduled_for = None
                if random.random() < 0.05:
                    status = 'scheduled'
                    scheduled_for = timezone.now() + timedelta(days=random.randint(1, 30))
                article = Article.objects.create(
                    author=user,
                    title=title,
                    dek=dek,
                    body=body,
                    status=status,
                    published_at=published_at,
                    scheduled_for=scheduled_for,
                    featured=featured,
                    cover_color=cover_color,
                    folio=folio,
                )
                article.tags.set(article_tags)
                articles.append(article)

        self.stdout.write(f'Created {len(articles)} articles.')

        # 5. Create Comments
        self.stdout.write('Creating comments...')
        comment_count = 0
        for article in articles:
            if article.status != 'published':
                continue
            num_comments = random.randint(0, 15)
            for _ in range(num_comments):
                author = random.choice(users)
                if author == article.author:
                    continue
                text = fake.paragraph(nb_sentences=random.randint(1, 4))
                parent = None
                if random.random() < 0.2:
                    existing = Comment.objects.filter(article=article).order_by('?').first()
                    if existing:
                        parent = existing
                Comment.objects.create(
                    article=article,
                    author=author,
                    parent=parent,
                    text=text,
                    is_approved=True
                )
                comment_count += 1
        self.stdout.write(f'Created {comment_count} comments.')

        # 6. Assign Claps & update counts
        self.stdout.write('Assigning claps...')
        for article in articles:
            if article.status != 'published':
                continue
            article.claps_count = random.randint(0, 200)
            article.comments_count = Comment.objects.filter(article=article).count()
            article.save(update_fields=['claps_count', 'comments_count'])

        # 7. Create Bookmarks
        self.stdout.write('Creating bookmarks...')
        bookmark_count = 0
        for article in articles:
            if article.status != 'published':
                continue
            num_bookmarks = random.randint(0, int(len(users)*0.3))
            bookmarks_users = random.sample(users, min(num_bookmarks, len(users)))
            for user in bookmarks_users:
                if user == article.author:
                    continue
                if not Bookmark.objects.filter(user=user, article=article).exists():
                    Bookmark.objects.create(user=user, article=article)
                    bookmark_count += 1
        self.stdout.write(f'Created {bookmark_count} bookmarks.')

        # 8. Create Notifications
        self.stdout.write('Creating notifications...')
        notification_count = 0
        for follow in Follow.objects.all():
            if random.random() < 0.3:
                Notification.objects.create(
                    user=follow.followed,
                    actor=follow.follower,
                    notification_type=Notification.Type.FOLLOW,
                    message=f"{follow.follower.name} started following you.",
                    link=f"/@{follow.follower.handle}/"
                )
                notification_count += 1
        for comment in Comment.objects.all():
            if comment.article.author != comment.author:
                if random.random() < 0.3:
                    Notification.objects.create(
                        user=comment.article.author,
                        actor=comment.author,
                        notification_type=Notification.Type.COMMENT,
                        target_type='article',
                        target_id=comment.article.id,
                        message=f"{comment.author.name} commented on your article: {comment.article.title}",
                        link=f"/article/{comment.article.id}/"
                    )
                    notification_count += 1
            if comment.parent and comment.parent.author != comment.author:
                if random.random() < 0.3:
                    Notification.objects.create(
                        user=comment.parent.author,
                        actor=comment.author,
                        notification_type=Notification.Type.COMMENT,
                        target_type='comment',
                        target_id=comment.id,
                        message=f"{comment.author.name} replied to your comment.",
                        link=f"/article/{comment.article.id}/"
                    )
                    notification_count += 1
        self.stdout.write(f'Created {notification_count} notifications.')

        # 9. Create Reading History
        self.stdout.write('Creating reading history...')
        history_count = 0
        for user in users:
            num_read = random.randint(0, 15)
            read_articles = random.sample(articles, min(num_read, len(articles)))
            for article in read_articles:
                if article.status != 'published':
                    continue
                if not ReadingHistory.objects.filter(user=user, article=article).exists():
                    ReadingHistory.objects.create(
                        user=user,
                        article=article,
                        read_count=random.randint(1, 5)
                    )
                    history_count += 1
        self.stdout.write(f'Created {history_count} reading history records.')

        # 10. Create Reports
        self.stdout.write('Creating reports...')
        report_count = 0
        for _ in range(random.randint(0, 30)):
            reporter = random.choice(users)
            target_type = random.choice(['article', 'comment'])
            if target_type == 'article':
                target = random.choice(articles)
                target_id = target.id
            else:
                comments_pool = Comment.objects.all()
                if comments_pool.exists():
                    target = random.choice(comments_pool)
                    target_id = target.id
                else:
                    continue
            reason = fake.paragraph(nb_sentences=2)
            Report.objects.create(
                reporter=reporter,
                target_type=target_type,
                target_id=target_id,
                reason=reason,
                status=random.choice(['pending', 'reviewed', 'dismissed'])
            )
            report_count += 1
        self.stdout.write(f'Created {report_count} reports.')

        # Update user article counts
        self.stdout.write('Updating user article counts...')
        for user in users:
            user.articles_count = Article.objects.filter(author=user).count()
            user.save(update_fields=['articles_count'])

        self.stdout.write('Sample data population complete!')