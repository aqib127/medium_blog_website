# The RAG pipeline stores embeddings in ChromaDB (an embedded vector store on
# disk), not in PostgreSQL. No Django models are needed here — article metadata
# and vectors are keyed by the articles.Article primary key.
