from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import User, UserSettings, Follow

@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        UserSettings.objects.create(user=instance)

@receiver(post_save, sender=Follow)
def update_follow_counts_on_create(sender, instance, created, **kwargs):
    if created:
        instance.follower.following_count += 1
        instance.follower.save(update_fields=['following_count'])
        instance.followed.followers_count += 1
        instance.followed.save(update_fields=['followers_count'])

@receiver(pre_delete, sender=Follow)
def update_follow_counts_on_delete(sender, instance, **kwargs):
    instance.follower.following_count -= 1
    instance.follower.save(update_fields=['following_count'])
    instance.followed.followers_count -= 1
    instance.followed.save(update_fields=['followers_count'])