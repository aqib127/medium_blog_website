from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from .models import Article
from users.models import User


@receiver(pre_save, sender=Article)
def calculate_read_mins(sender, instance, **kwargs):
    word_count = len(instance.body.split())
    instance.read_mins = max(1, round(word_count / 200))


# `articles_count` counts ALL articles authored (drafts included), so no
# status-transition logic is required — a create increments, a delete
# decrements, atomically via F().
@receiver(post_save, sender=Article)
def increment_articles_count(sender, instance, created, **kwargs):
    if created:
        User.objects.filter(pk=instance.author_id).update(
            articles_count=F('articles_count') + 1
        )


@receiver(post_delete, sender=Article)
def decrement_articles_count(sender, instance, **kwargs):
    User.objects.filter(pk=instance.author_id).update(
        articles_count=F('articles_count') - 1
    )
