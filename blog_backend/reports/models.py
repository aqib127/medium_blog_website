from django.db import models
from core.models import BaseModel
from users.models import User

class Report(BaseModel):
    class TargetType(models.TextChoices):
        ARTICLE = 'article', 'Article'
        COMMENT = 'comment', 'Comment'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        REVIEWED = 'reviewed', 'Reviewed'
        DISMISSED = 'dismissed', 'Dismissed'

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    target_type = models.CharField(max_length=20, choices=TargetType.choices)
    target_id = models.PositiveIntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    def __str__(self):
        return f"Report by {self.reporter.name} on {self.target_type} {self.target_id}"