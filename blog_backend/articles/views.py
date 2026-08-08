from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from .models import Article, Tag, Clap
from .serializers import ArticleSerializer, ArticleCreateUpdateSerializer, TagSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'dek', 'body', 'tags__name', 'author__name', 'author__handle']
    ordering_fields = ['created_at', 'published_at', 'claps_count', 'view_count']

    def get_serializer_class(self):
        """
        FIX: create/update requests must use ArticleCreateUpdateSerializer
        (it has writable `image` and `tag_ids` fields). The default
        ArticleSerializer is read-focused (nested author/tags, computed
        image_url) and was silently dropping the uploaded image and tags
        on every publish/save-draft request — DRF ignores fields that
        aren't declared on the serializer being used.
        """
        if self.action in ('create', 'update', 'partial_update'):
            return ArticleCreateUpdateSerializer
        return ArticleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='published')
        else:
            queryset = queryset.filter(status='published') | queryset.filter(
                author=self.request.user
            ).exclude(status='archived')

        tag_slug = self.request.query_params.get('tags__slug')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        status_param = self.request.query_params.get('status')
        if status_param == 'draft' and self.request.user.is_authenticated:
            queryset = queryset.filter(author=self.request.user, status='draft')

        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Return the full, read-shaped article (with image_url, nested tags,
        nested author) after create — not the write-serializer's bare
        shape — so the frontend always gets a complete, display-ready
        object straight after publish/save-draft, without needing a
        second GET request.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        read_serializer = ArticleSerializer(instance, context=self.get_serializer_context())
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        read_serializer = ArticleSerializer(serializer.instance, context=self.get_serializer_context())
        return Response(read_serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        article = (
            self.get_queryset()
            .filter(status='published', featured=True)
            .order_by('-published_at')
            .first()
        )
        if not article:
            article = (
                self.get_queryset()
                .filter(status='published')
                .order_by('-published_at')
                .first()
            )
        if not article:
            return Response(None)
        serializer = ArticleSerializer(article, context=self.get_serializer_context())

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        trending_articles = self.get_queryset().filter(status='published').order_by('-view_count')[:5]
        serializer = ArticleSerializer(trending_articles, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def clap(self, request, pk=None):
        """
        Toggle a clap for the current user on this article (like/unlike
        behaviour): first POST creates the clap, a second POST removes it.
        Keeps Article.claps_count in sync as a denormalized counter.
        """
        article = self.get_object()
        clap_qs = Clap.objects.filter(user=request.user, article=article)

        if clap_qs.exists():
            clap_qs.delete()
            clapped = False
        else:
            Clap.objects.create(user=request.user, article=article)
            clapped = True

        article.claps_count = article.claps.count()
        article.save(update_fields=['claps_count'])

        return Response(
            {'claps_count': article.claps_count, 'clapped': clapped},
            status=status.HTTP_200_OK,
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().annotate(num_articles=Count('articles')).order_by('name')
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None