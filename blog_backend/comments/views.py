from rest_framework import viewsets, permissions
from .models import Comment
from .serializers import CommentSerializer
from core.permissions import IsOwnerOrReadOnly

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.filter(parent__isnull=True)
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        article_id = self.request.query_params.get('article')
        if article_id:
            qs = qs.filter(article_id=article_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)