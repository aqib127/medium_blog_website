from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('api/v1/auth/', include('users.urls')),

    # User profile
    path('api/v1/users/', include('users.urls_profile')),

    # Articles + tags
    path('api/v1/', include('articles.urls')),

    # Other APIs
    path('api/v1/bookmarks/', include('bookmarks.urls')),
    path('api/v1/comments/', include('comments.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    path('api/v1/history/', include('reading_history.urls')),
    path('api/v1/reports/', include('reports.urls')),

    # New RAG endpoint – LangChain + pgvector with streaming
    path('api/v1/rag/', include('rag_langchain.urls')),

    # OpenAPI schema
    path(
        'api/schema/',
        SpectacularAPIView.as_view(),
        name='schema',
    ),
    # Swagger UI
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls))
        ] + urlpatterns