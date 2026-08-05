from django.contrib import admin
from .models import Tag, Article, ArticleTag, ArticleImage, Clap


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'published_at', 'claps_count', 'comments_count')
    list_filter = ('status', 'featured', 'tags')
    search_fields = ('title', 'dek', 'body')
    readonly_fields = ('claps_count', 'comments_count', 'view_count')


@admin.register(ArticleTag)
class ArticleTagAdmin(admin.ModelAdmin):
    list_display = ('article', 'tag')


@admin.register(ArticleImage)
class ArticleImageAdmin(admin.ModelAdmin):
    list_display = ('article', 'image', 'order')


@admin.register(Clap)
class ClapAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'created_at')
    search_fields = ('user__name', 'article__title')
