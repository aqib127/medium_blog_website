from django.urls import path
from .views import ChatStreamView, ReindexView

urlpatterns = [
    path('chat/stream/', ChatStreamView.as_view(), name='chat-stream'),
    path('reindex/', ReindexView.as_view(), name='reindex'),
]
