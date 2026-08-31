from langchain_ollama import OllamaEmbeddings
from django.conf import settings

def get_embeddings():
    return OllamaEmbeddings(
        model=settings.OLLAMA_EMBED_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    
    )
