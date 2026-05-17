"""
RAG Retriever — semantic search over indexed code chunks using pgvector.
"""

import logging
from typing import Any

import google.generativeai as genai
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_EMBEDDING_MODEL = "models/text-embedding-004"
_EMBEDDING_DIM = 768


class RAGRetriever:
    """Search indexed code chunks by semantic similarity."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)

    async def search(
        self,
        query: str,
        session_id: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Return the top_k most relevant code chunks for the query."""
        try:
            embedding = await self._embed_query(query)
            vector_str = "[" + ",".join(str(v) for v in embedding) + "]"

            result = await self._db.execute(
                text("""
                    SELECT
                        id,
                        file_path,
                        content,
                        1 - (embedding <=> :embedding::vector) AS similarity
                    FROM rag_chunks
                    WHERE session_id = :session_id
                    ORDER BY embedding <=> :embedding::vector
                    LIMIT :top_k
                """),
                {
                    "embedding": vector_str,
                    "session_id": session_id,
                    "top_k": top_k,
                },
            )
            rows = result.fetchall()
            return [
                {
                    "id": str(row.id),
                    "file_path": row.file_path,
                    "content": row.content,
                    "similarity": float(row.similarity),
                }
                for row in rows
            ]
        except Exception as exc:
            logger.error(f"RAG search failed: {exc}")
            return []

    async def _embed_query(self, query: str) -> list[float]:
        """Embed a search query using Gemini text-embedding-004."""
        if not settings.GOOGLE_API_KEY:
            return [0.0] * _EMBEDDING_DIM
        try:
            result = genai.embed_content(
                model=_EMBEDDING_MODEL,
                content=query,
                task_type="retrieval_query",
            )
            return result["embedding"]
        except Exception as exc:
            logger.error(f"Query embedding failed: {exc}")
            return [0.0] * _EMBEDDING_DIM
