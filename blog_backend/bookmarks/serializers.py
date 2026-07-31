from rest_framework import serializers
from .models import Bookmark
from articles.serializers import ArticleSerializer

class BookmarkSerializer(serializers.ModelSerializer):
    article = ArticleSerializer(read_only=True)
    article_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = Bookmark
        fields = ('id', 'user', 'article', 'article_id', 'created_at')
        read_only_fields = ('user', 'created_at')

    def create(self, validated_data):
        article_id = validated_data.pop('article_id')
        from articles.models import Article
        article = Article.objects.get(id=article_id)
        validated_data['article'] = article
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)