from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.db import IntegrityError
from .models import Bookmark
from .serializers import BookmarkSerializer

class BookmarkViewSet(viewsets.ModelViewSet):
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for bookmarks

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        if 'article_id' not in request.data:
            return Response({'detail': 'article_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response({'detail': 'Bookmark already exists.'}, status=status.HTTP_409_CONFLICT)

    def destroy(self, request, *args, **kwargs):
        article_id = self.kwargs.get('pk')
        try:
            bookmark = Bookmark.objects.get(user=request.user, article_id=article_id)
        except Bookmark.DoesNotExist:
            return Response({'detail': 'Bookmark not found.'}, status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(bookmark)
        return Response(status=status.HTTP_204_NO_CONTENT)