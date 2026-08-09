from django.utils import timezone
from rest_framework import serializers
from .models import Tag, Article, ArticleTag, ArticleImage, Clap
from .topic_images import build_topic_image_url
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
    """
    READ-focused serializer: nested author/tags, computed image_url,
    computed clap/bookmark flags. Used for list/retrieve/featured/trending.
    Intentionally does NOT expose writable `image` or `tag_ids` — those
    live on ArticleCreateUpdateSerializer.
    """
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    images = ArticleImageSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    is_clapped = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = (
            'id', 'author', 'title', 'dek', 'body', 'status',
            'published_at', 'scheduled_for', 'featured', 'cover_color',
            'folio', 'read_mins', 'claps_count', 'comments_count',
            'view_count', 'tags', 'images', 'image_url',
            'is_clapped', 'is_bookmarked',
            'created_at', 'updated_at'
        )

    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url

        tag_names = [t.name for t in obj.tags.all()]
        return build_topic_image_url(obj.id, tag_names)

    def get_is_clapped(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return obj.claps.filter(user=user).exists()
        return False

    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return obj.bookmarks.filter(user=user).exists()
        return False


class ArticleCreateUpdateSerializer(serializers.ModelSerializer):
    """
    WRITE-focused serializer: this is the one that must be wired into
    ArticleViewSet for create/update — it's the only serializer that
    actually accepts `image` (multipart file) and `tag_ids` (list of tag
    IDs) from the request body.
    """
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    tags = TagSerializer(many=True, read_only=True)
    image = serializers.ImageField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = Article
        fields = (
            'id', 'author', 'title', 'dek', 'body', 'status',
            'published_at', 'scheduled_for', 'featured', 'cover_color',
            'folio', 'read_mins', 'tag_ids', 'tags', 'image',
            'created_at', 'updated_at'
        )
        read_only_fields = ('author', 'claps_count', 'comments_count', 'view_count', 'created_at', 'updated_at')

    def _publish_if_needed(self, instance, previous_status=None):
        """
        FIX: published_at was never set when a draft was published, so the
        featured/trending endpoints (which sort by -published_at) never
        surfaced newly published stories, and NULLs sorted last. Set the
        publish timestamp the first time a story transitions into the
        'published' state, and clear it if it's unpublished again.
        """
        new_status = getattr(instance, 'status', None)
        if new_status == Article.Status.PUBLISHED and previous_status != Article.Status.PUBLISHED:
            if not instance.published_at:
                instance.published_at = timezone.now()
        elif new_status != Article.Status.PUBLISHED:
            instance.published_at = None
        return instance

    def create(self, validated_data):
        image_file = validated_data.pop('image', None)
        tag_ids = validated_data.pop('tag_ids', [])
        article = Article.objects.create(**validated_data)
        self._publish_if_needed(article)
        if image_file:
            article.image = image_file
        if tag_ids:
            article.tags.set(tag_ids)
        article.save()
        return article

    def update(self, instance, validated_data):
        image_file = validated_data.pop('image', None)
        tag_ids = validated_data.pop('tag_ids', None)

        previous_status = instance.status
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        self._publish_if_needed(instance, previous_status)

        if image_file is not None:
            instance.image = image_file
        elif image_file is None and 'image' in self.initial_data:
            instance.image = None
        instance.save()

        if tag_ids is not None:
            instance.tags.set(tag_ids)
        return instance


class ClapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clap
        fields = ('id', 'user', 'article', 'created_at')
        read_only_fields = ('user', 'created_at')