from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, TagViewSet

router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')

urlpatterns = [
    # Custom path must be BEFORE the router include
    path('articles/tags/', TagViewSet.as_view({'get': 'list'}), name='article-tags'),
    path('', include(router.urls)),
]