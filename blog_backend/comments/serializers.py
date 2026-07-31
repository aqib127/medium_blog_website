from rest_framework import serializers
from .models import Comment
from users.serializers import UserSerializer

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('id', 'article', 'author', 'parent', 'text', 'is_approved', 'created_at', 'updated_at', 'replies')
        read_only_fields = ('is_approved', 'created_at', 'updated_at')

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
