from rest_framework import serializers
from .models import NewsletterSubscriber


class SubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    source = serializers.CharField(max_length=50, required=False, allow_blank=True, default='website')


class ConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=256)


class UnsubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    token = serializers.CharField(max_length=256, required=False)

    def validate(self, data):
        if not data.get('email') and not data.get('token'):
            raise serializers.ValidationError(
                "Either 'email' or 'token' is required."
            )
        return data


class SubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = ['id', 'email', 'name', 'is_confirmed', 'is_active', 'confirmed_at', 'created_at']
        read_only_fields = fields
