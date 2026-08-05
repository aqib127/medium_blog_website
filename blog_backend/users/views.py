from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from .models import User, Follow
from .serializers import (
    UserSerializer, UserProfileUpdateSerializer,
    RegisterSerializer, TokenResponseSerializer,
    FollowSerializer, CustomTokenObtainPairSerializer
)
from core.permissions import IsOwnerOrReadOnly
from articles.serializers import ArticleSerializer
from articles.models import Article
import os

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        user_serializer = UserSerializer(user, context={'request': request})
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user_serializer.data
        }, status=status.HTTP_201_CREATED)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class MeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_context(self):
        return {'request': self.request}

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'detail': 'Refresh token required.'}, status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'handle'
    lookup_url_kwarg = 'handle'

    def get_serializer_context(self):
        return {'request': self.request}

class UserStoriesView(generics.ListAPIView):
    serializer_class = ArticleSerializer

    def get_queryset(self):
        handle = self.kwargs['handle']
        user = get_object_or_404(User, handle=handle)
        return Article.objects.filter(author=user, status='published').order_by('-published_at')

class FollowersView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        handle = self.kwargs['handle']
        user = get_object_or_404(User, handle=handle)
        followers = user.followers_set.all().select_related('follower')
        return [f.follower for f in followers]

    def get_serializer_context(self):
        return {'request': self.request}

class FollowingView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        handle = self.kwargs['handle']
        user = get_object_or_404(User, handle=handle)
        following = user.following_set.all().select_related('followed')
        return [f.followed for f in following]

    def get_serializer_context(self):
        return {'request': self.request}

class FollowToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, handle):
        target = get_object_or_404(User, handle=handle)
        if target == request.user:
            return Response({'detail': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        follow, created = Follow.objects.get_or_create(follower=request.user, followed=target)
        if not created:
            return Response({'detail': 'Already following.'}, status=status.HTTP_409_CONFLICT)
        return Response({'detail': f'You are now following @{target.handle}.'}, status=status.HTTP_201_CREATED)

    def delete(self, request, handle):
        target = get_object_or_404(User, handle=handle)
        follow = Follow.objects.filter(follower=request.user, followed=target).first()
        if not follow:
            return Response({'detail': 'Not following.'}, status=status.HTTP_404_NOT_FOUND)
        follow.delete()
        return Response({'detail': f'Unfollowed @{target.handle}.'}, status=status.HTTP_204_NO_CONTENT)

class ProfileUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileUpdateSerializer
    lookup_field = 'handle'
    lookup_url_kwarg = 'handle'

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def get_object(self):
        user = super().get_object()
        if user != self.request.user:
            raise PermissionDenied('You can only update your own profile.')
        return user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        user_serializer = UserSerializer(instance, context={'request': request})
        return Response(user_serializer.data)

class AvatarUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, handle):
        user = get_object_or_404(User, handle=handle)
        if user != request.user:
            raise PermissionDenied('You can only update your own avatar.')

        # Handle removal via JSON: { "avatar": null }
        if request.content_type == 'application/json':
            data = request.data
            if data.get('avatar') is None:
                if user.avatar:
                    if os.path.isfile(user.avatar.path):
                        os.remove(user.avatar.path)
                    user.avatar = None
                    user.save(update_fields=['avatar'])
                return Response({'avatar_url': None})
            return Response({'detail': 'Invalid JSON payload.'}, status=status.HTTP_400_BAD_REQUEST)

        # Otherwise handle file upload
        if 'avatar' not in request.FILES:
            return Response({'detail': 'No avatar file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        user.avatar = request.FILES['avatar']
        user.save()
        avatar_url = request.build_absolute_uri(user.avatar.url) if user.avatar else None
        return Response({'avatar_url': avatar_url})