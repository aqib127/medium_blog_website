from django.urls import path

from .views import ReindexView, SemanticSearchView

urlpatterns = [
    path('reindex/', ReindexView.as_view(), name='rag-reindex'),
    path('search/', SemanticSearchView.as_view(), name='rag-search'),
]
