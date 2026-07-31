from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import BaseModel
from .managers import UserManager

class User(AbstractUser, BaseModel):
    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150)
    handle = models.CharField(max_length=100, unique=True)
    bio = models.TextField(blank=True, default='')
    location = models.CharField(max_length=100, blank=True, default='')
    twitter = models.CharField(max_length=100, blank=True, default='')
    github = models.CharField(max_length=100, blank=True, default='')
    website = models.URLField(max_length=200, blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    avatar_color = models.CharField(max_length=7, default='#1F4E4A')
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    articles_count = models.PositiveIntegerField(default=0)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def initials(self):
        return ''.join([part[0].upper() for part in self.name.split()[:2]])

    def save(self, *args, **kwargs):
        if not self.handle:
            from core.utils import generate_unique_slug
            self.handle = generate_unique_slug(User, 'handle', self.name)
        super().save(*args, **kwargs)

class UserSettings(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=False)
    preferences = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Settings for {self.user.email}"

class Follow(BaseModel):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_set')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers_set')

    class Meta:
        unique_together = ('follower', 'followed')

    def __str__(self):
        return f"{self.follower.email} follows {self.followed.email}"