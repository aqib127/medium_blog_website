from rest_framework import serializers
from .models import Notification
from users.serializers import UserSerializer

class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ('id', 'user', 'actor', 'notification_type', 'target_type', 'target_id', 'message', 'link', 'read_at', 'created_at')
        read_only_fields = ('user', 'actor', 'created_at')
