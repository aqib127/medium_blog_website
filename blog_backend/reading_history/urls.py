from rest_framework.routers import DefaultRouter
from .views import ReadingHistoryViewSet

router = DefaultRouter()
router.register(r'', ReadingHistoryViewSet, basename='readinghistory')

urlpatterns = router.urls
