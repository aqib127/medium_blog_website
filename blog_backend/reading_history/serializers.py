from rest_framework import serializers
from .models import ReadingHistory
from articles.serializers import ArticleSerializer

class ReadingHistorySerializer(serializers.ModelSerializer):
    article = ArticleSerializer(read_only=True)

    class Meta:
        model = ReadingHistory
        fields = ('id', 'user', 'article', 'last_read_at', 'read_count')
        read_only_fields = ('user', 'last_read_at', 'read_count')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        article = validated_data['article']
        instance, created = ReadingHistory.objects.get_or_create(
            user=self.context['request'].user,
            article=article,
            defaults=validated_data
        )
        if not created:
            instance.read_count += 1
            instance.save(update_fields=['read_count'])
        return instance
