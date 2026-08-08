from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth (register, login, refresh, verify, logout, me)
    path('api/v1/auth/', include('users.urls')),

    # User profile endpoints (stories, followers, following, follow, update, avatar)
    path('api/v1/users/', include('users.urls_profile')),

    # Articles + tags
    path('api/v1/', include('articles.urls')),

    path('api/v1/bookmarks/', include('bookmarks.urls')),
    path('api/v1/comments/', include('comments.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    path('api/v1/history/', include('reading_history.urls')),
    path('api/v1/reports/', include('reports.urls')),
    path('api/v1/chatbot/', include('chatbot.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar
    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns