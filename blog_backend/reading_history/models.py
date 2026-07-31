from django.db import models
from core.models import BaseModel
from users.models import User
from articles.models import Article

class ReadingHistory(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_history')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='reading_history')
    last_read_at = models.DateTimeField(auto_now=True)
    read_count = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('user', 'article')

    def __str__(self):
        return f"{self.user.name} read {self.article.title}"