from rest_framework import serializers
from .models import Tag, Article, ArticleTag, ArticleImage, Clap
from users.serializers import UserSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'description')


class ArticleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleImage
        fields = ('id', 'image', 'caption', 'order')


class ArticleSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    images = ArticleImageSerializer(many=True, read_only=True)
    is_clapped = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = (
            'id', 'author', 'title', 'dek', 'body', 'status',
            'published_at', 'scheduled_for', 'featured', 'cover_color',
            'folio', 'read_mins', 'claps_count', 'comments_count',
            'view_count', 'tags', 'images', 'is_clapped', 'is_bookmarked',
            'created_at', 'updated_at'
        )

    def get_is_clapped(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            # Prefetched via viewset when possible; falls back to a query.
            return obj.claps.filter(user=user).exists()
        return False

    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return obj.bookmarks.filter(user=user).exists()
        return False


class ArticleCreateUpdateSerializer(serializers.ModelSerializer):
    tag_ids = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = (
            'id', 'author', 'title', 'dek', 'body', 'status',
            'published_at', 'scheduled_for', 'featured', 'cover_color',
            'folio', 'read_mins', 'tag_ids', 'tags',
            'created_at', 'updated_at'
        )
        read_only_fields = ('author', 'claps_count', 'comments_count', 'view_count', 'created_at', 'updated_at')

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        article = Article.objects.create(**validated_data)
        if tag_ids:
            article.tags.set(tag_ids)
        return article

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        return instance


class ClapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clap
        fields = ('id', 'user', 'article', 'created_at')
        read_only_fields = ('user', 'created_at')
