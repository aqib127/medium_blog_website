from django.db import models
from core.models import BaseModel
from users.models import User
from articles.models import Article

class Bookmark(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='bookmarks')

    class Meta:
        unique_together = ('user', 'article')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.name} bookmarked {self.article.title}"