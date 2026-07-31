from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Notification
from users.models import Follow
from articles.models import Article
from comments.models import Comment
from bookmarks.models import Bookmark

@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.followed,
            actor=instance.follower,
            notification_type=Notification.Type.FOLLOW,
            message=f"{instance.follower.name} started following you."
        )

@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        if instance.article.author != instance.author:
            Notification.objects.create(
                user=instance.article.author,
                actor=instance.author,
                notification_type=Notification.Type.COMMENT,
                target_type='article',
                target_id=instance.article.id,
                message=f"{instance.author.name} commented on your article: {instance.article.title}",
                link=f"/article/{instance.article.id}/"
            )
        if instance.parent and instance.parent.author != instance.author:
            Notification.objects.create(
                user=instance.parent.author,
                actor=instance.author,
                notification_type=Notification.Type.COMMENT,
                target_type='comment',
                target_id=instance.id,
                message=f"{instance.author.name} replied to your comment.",
                link=f"/article/{instance.article.id}/"
            )
