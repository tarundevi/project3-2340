import logging

logger = logging.getLogger(__name__)


def retrieve_context(query: str) -> list[str]:
    try:
        import chromadb
        from app.config import settings

        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        collection = client.get_collection("nutrition_docs")
        results = collection.query(query_texts=[query], n_results=3)
        return results["documents"][0] if results["documents"] else []
    except Exception as e:
        logger.warning(f"ChromaDB not available, returning empty context: {e}")
        return []
