from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def health_check(request):
    return JsonResponse({
        "status": "ok",
        "service": "Medium Blog API",
    })


urlpatterns = [
    path('', health_check, name='health-check'),
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('users.urls')),
    path('api/v1/users/', include('users.urls_profile')),
    path('api/v1/', include('articles.urls')),
    path('api/v1/bookmarks/', include('bookmarks.urls')),
    path('api/v1/comments/', include('comments.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    path('api/v1/history/', include('reading_history.urls')),
    path('api/v1/reports/', include('reports.urls')),
    path('api/v1/rag/', include('rag_langchain.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass