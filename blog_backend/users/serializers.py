from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from .models import User, UserSettings, Follow

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'name', 'handle', 'bio', 'location',
            'twitter', 'github', 'website', 'avatar', 'avatar_color',
            'followers_count', 'following_count', 'articles_count',
            'date_joined'
        )
        read_only_fields = (
            'id', 'email', 'handle', 'followers_count',
            'following_count', 'articles_count', 'date_joined'
        )

    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            # Fallback: relative URL with MEDIA_URL
            return obj.avatar.url
        return None

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('name', 'bio', 'location', 'twitter', 'github', 'website', 'avatar_color')
        extra_kwargs = {
            'name': {'required': False},
            'bio': {'required': False},
            'location': {'required': False},
            'twitter': {'required': False},
            'github': {'required': False},
            'website': {'required': False},
            'avatar_color': {'required': False},
        }

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    name = serializers.CharField(required=True)
    handle = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('email', 'name', 'handle', 'password')

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            name=validated_data['name'],
            handle=validated_data.get('handle', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()

class FollowSerializer(serializers.ModelSerializer):
    follower = UserSerializer(read_only=True)
    followed = UserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ('id', 'follower', 'followed', 'created_at')
        read_only_fields = ('follower', 'followed', 'created_at')

# Custom JWT serializer for email login
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        return super().get_token(user)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        if not email or not password:
            raise serializers.ValidationError('Email and password are required.')
        
        from django.contrib.auth import authenticate
        user = authenticate(request=self.context.get('request'),
                            username=email, password=password)
        if not user:
            raise serializers.ValidationError('Invalid credentials.')
        
        refresh = self.get_token(user)
        # Use UserSerializer with request context
        user_data = UserSerializer(user, context=self.context).data
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user_data
        }