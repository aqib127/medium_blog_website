from django.urls import path
from .views import (
    ChatStreamView,      # existing
    ReindexView,         # existing
    chat_with_actions,   # NEW
    rag_health,          # NEW
)

app_name = "rag_langchain"

urlpatterns = [
    # ---- EXISTING ----
    path("chat/stream/", ChatStreamView.as_view(), name="chat-stream"),
    path("reindex/", ReindexView.as_view(), name="reindex"),

    # ---- NEW ----
    path("chat/", chat_with_actions, name="chat-actions"),
    path("health/", rag_health, name="health"),
]