from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.db.models import F
from .models import User, UserSettings, Follow

@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        UserSettings.objects.create(user=instance)

@receiver(post_save, sender=Follow)
def update_follow_counts_on_create(sender, instance, created, **kwargs):
    if created:
        # Atomic increments via F() — no read-modify-write race.
        User.objects.filter(pk=instance.follower_id).update(
            following_count=F('following_count') + 1
        )
        User.objects.filter(pk=instance.followed_id).update(
            followers_count=F('followers_count') + 1
        )

@receiver(pre_delete, sender=Follow)
def update_follow_counts_on_delete(sender, instance, **kwargs):
    User.objects.filter(pk=instance.follower_id).update(
        following_count=F('following_count') - 1
    )
    User.objects.filter(pk=instance.followed_id).update(
        followers_count=F('followers_count') - 1
    )
