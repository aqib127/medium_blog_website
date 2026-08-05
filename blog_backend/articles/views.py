from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from .models import Article, Tag, Clap
from .serializers import ArticleSerializer, ArticleCreateUpdateSerializer, TagSerializer
from core.permissions import IsOwnerOrReadOnly
from core.pagination import StandardResultsSetPagination


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'author__handle', 'tags__slug']
    search_fields = ['title', 'dek', 'body']
    ordering_fields = ['created_at', 'published_at', 'claps_count', 'comments_count']
    ordering = ['-published_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ArticleCreateUpdateSerializer
        return ArticleSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == 'list':
            user = self.request.user
            status_param = self.request.query_params.get('status')
            # A signed-in user asking for status=draft only ever gets their
            # OWN drafts — drafts are never publicly listable.
            if status_param == 'draft':
                if user.is_authenticated:
                    return qs.filter(author=user, status=Article.Status.DRAFT)
                return qs.none()
            return qs.filter(status=Article.Status.PUBLISHED)
        return qs

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def clap(self, request, pk=None):
        article = self.get_object()
        clap, created = Clap.objects.get_or_create(user=request.user, article=article)
        if created:
            Article.objects.filter(pk=article.pk).update(claps_count=models.F('claps_count') + 1)
            clapped = True
        else:
            clap.delete()
            Article.objects.filter(pk=article.pk).update(claps_count=models.F('claps_count') - 1)
            clapped = False
        article.refresh_from_db(fields=['claps_count'])
        return Response({'claps_count': article.claps_count, 'clapped': clapped})

    @action(detail=False, methods=['get'])
    def featured(self, request):
        article = Article.objects.filter(featured=True, status=Article.Status.PUBLISHED).first()
        if not article:
            return Response({'detail': 'No featured article found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(article)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        limit = request.query_params.get('limit', 5)
        try:
            limit = int(limit)
        except ValueError:
            limit = 5
        articles = Article.objects.filter(status=Article.Status.PUBLISHED).order_by('-claps_count')[:limit]
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
