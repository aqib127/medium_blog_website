from django.db import models
from django.utils.text import slugify
from core.models import BaseModel
from users.models import User


class Tag(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    description = models.TextField(blank=True, default='')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Article(BaseModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        SCHEDULED = 'scheduled', 'Scheduled'
        ARCHIVED = 'archived', 'Archived'

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=300)
    dek = models.TextField(blank=True, default='')
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    featured = models.BooleanField(default=False)
    cover_color = models.CharField(max_length=7, default='#1F4E4A')
    folio = models.CharField(max_length=10, blank=True, default='')
    read_mins = models.PositiveSmallIntegerField(default=1)
    claps_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)

    tags = models.ManyToManyField(Tag, through='ArticleTag', related_name='articles')

    def __str__(self):
        return self.title


class ArticleTag(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('article', 'tag')


class ArticleImage(BaseModel):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='article_images/')
    caption = models.CharField(max_length=200, blank=True, default='')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']


class Clap(BaseModel):
    """
    Tracks a single clap per (user, article) pair. A user can clap for an
    article only once — clicking again removes the clap (like/unlike
    behaviour). Article.claps_count is kept as a denormalized counter that
    is updated whenever a Clap is created or deleted.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claps')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='claps')

    class Meta:
        unique_together = ('user', 'article')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.name} clapped {self.article.title}"
