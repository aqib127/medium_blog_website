from django.db import models
from core.models import BaseModel
from users.models import User

class Notification(BaseModel):
    class Type(models.TextChoices):
        FOLLOW = 'follow', 'Follow'
        COMMENT = 'comment', 'Comment'
        CLAP = 'clap', 'Clap'
        BOOKMARK = 'bookmark', 'Bookmark'
        MENTION = 'mention', 'Mention'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actor_notifications')
    notification_type = models.CharField(max_length=20, choices=Type.choices)
    target_type = models.CharField(max_length=20, blank=True)  # 'article' or 'comment'
    target_id = models.PositiveIntegerField(null=True, blank=True)
    message = models.TextField(blank=True, default='')
    link = models.URLField(max_length=500, blank=True, default='')
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.notification_type} for {self.user.email}"