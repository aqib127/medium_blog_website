from django.db import migrations

# Mirror core/management/commands/populate_db.py TOPICS so a fresh deploy has
# tags to select and display without running the (destructive) seed command.
DEFAULT_TAGS = [
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


def seed_tags(apps, schema_editor):
    Tag = apps.get_model('articles', 'Tag')
    for name, slug in DEFAULT_TAGS:
        Tag.objects.get_or_create(name=name, defaults={'slug': slug})


def unseed_tags(apps, schema_editor):
    Tag = apps.get_model('articles', 'Tag')
    Tag.objects.filter(name__in=[name for name, _ in DEFAULT_TAGS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('articles', '0004_alter_article_cover_color'),
    ]

    operations = [
        migrations.RunPython(seed_tags, unseed_tags),
    ]
