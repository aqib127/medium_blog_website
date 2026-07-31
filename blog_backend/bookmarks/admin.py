from django.contrib import admin
from .models import Bookmark

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'created_at')