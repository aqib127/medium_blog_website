from langchain_postgres import PGVector
from django.conf import settings
from .embeddings import get_embeddings

COLLECTION_NAME = settings.PGVECTOR_COLLECTION_NAME
CONNECTION_STRING = settings.PGVECTOR_CONNECTION_STRING

def get_vectorstore():
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
        use_jsonb=True,
    )

def get_retriever():
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.RAG_TOP_K},
    )
