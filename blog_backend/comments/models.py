from django.db import models
from core.models import BaseModel
from users.models import User
from articles.models import Article

class Comment(BaseModel):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    text = models.TextField()
    is_approved = models.BooleanField(default=True)

    def __str__(self):
        return f"Comment by {self.author.name} on {self.article.title}"