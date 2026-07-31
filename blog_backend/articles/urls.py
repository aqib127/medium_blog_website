from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, TagViewSet

router = DefaultRouter()
router.register(r'', ArticleViewSet, basename='article')

urlpatterns = [
    # Explicit paths for custom actions (fallback)
    path('featured/', ArticleViewSet.as_view({'get': 'featured'}), name='article-featured'),
    path('trending/', ArticleViewSet.as_view({'get': 'trending'}), name='article-trending'),
    # Tag endpoints
    path('tags/', TagViewSet.as_view({'get': 'list'}), name='tag-list'),
    path('tags/<int:pk>/', TagViewSet.as_view({'get': 'retrieve'}), name='tag-detail'),
    # All other CRUD + clap via router
    path('', include(router.urls)),
]