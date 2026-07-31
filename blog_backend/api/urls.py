from django.urls import path, include

app_name = 'api'

urlpatterns = [
    path('auth/', include('users.urls')),
    path('users/', include('users.urls_profile')),
    path('articles/', include('articles.urls')),
    path('comments/', include('comments.urls')),
    path('bookmarks/', include('bookmarks.urls')),
    path('notifications/', include('notifications.urls')),
    path('history/', include('reading_history.urls')),
    path('reports/', include('reports.urls')),
]