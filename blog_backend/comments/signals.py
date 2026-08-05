from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from .models import Comment

@receiver(post_save, sender=Comment)
def increment_comment_count(sender, instance, created, **kwargs):
    if created:
        Article = instance.article.__class__
        Article.objects.filter(pk=instance.article.pk).update(
            comments_count=F('comments_count') + 1
        )

@receiver(post_delete, sender=Comment)
def decrement_comment_count(sender, instance, **kwargs):
    Article = instance.article.__class__
    Article.objects.filter(pk=instance.article.pk).update(
        comments_count=F('comments_count') - 1
    )