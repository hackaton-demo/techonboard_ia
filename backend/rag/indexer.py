"""
RAG Indexer — clones a git repository, chunks the code files,
generates Gemini text-embedding-004 embeddings (768-dim), and
stores them in pgvector.
"""

import logging
import os
import re
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any

import google.generativeai as genai
from git import Repo, InvalidGitRepositoryError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Gemini embedding model
_EMBEDDING_MODEL = "models/text-embedding-004"
_EMBEDDING_DIM = 768

# File extensions to index
_CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".go", ".java", ".rb", ".rs", ".cs",
    ".md", ".yaml", ".yml", ".json", ".toml",
    ".sql", ".sh",
}
_MAX_CHUNK_CHARS = 1500
_CHUNK_OVERLAP = 200


class RAGIndexer:
    """Clone a repo and push code chunks with embeddings into pgvector."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)

    # ── Public API ────────────────────────────────────────────────────────────

    async def clone_repository(self, repo_url: str, target_dir: str | None = None) -> str:
        """Clone a git repo and return the local path."""
        if target_dir is None:
            target_dir = tempfile.mkdtemp(prefix="techonboard_rag_")

        try:
            logger.info(f"Cloning {repo_url} -> {target_dir}")
            Repo.clone_from(repo_url, target_dir, depth=1)
            return target_dir
        except Exception as exc:
            logger.error(f"Failed to clone {repo_url}: {exc}")
            raise

    async def index_repository(self, repo_path: str, session_id: str) -> int:
        """Index all code files in a cloned repository.

        Returns the number of chunks indexed.
        """
        # Ensure the pgvector table exists
        await self._ensure_table()

        chunks = list(self._collect_chunks(repo_path))
        if not chunks:
            logger.warning(f"No indexable files found in {repo_path}")
            return 0

        logger.info(f"Indexing {len(chunks)} chunks for session {session_id}")
        inserted = 0

        for i in range(0, len(chunks), 10):  # batch in groups of 10
            batch = chunks[i : i + 10]
            try:
                embeddings = await self._embed_batch([c["content"] for c in batch])
                for chunk, embedding in zip(batch, embeddings):
                    await self._insert_chunk(
                        session_id=session_id,
                        file_path=chunk["file_path"],
                        content=chunk["content"],
                        embedding=embedding,
                    )
                    inserted += 1
            except Exception as exc:
                logger.error(f"Failed to index batch {i}-{i+10}: {exc}")

        await self._db.commit()
        logger.info(f"Indexed {inserted} chunks for session {session_id}")
        return inserted

    # ── Internals ─────────────────────────────────────────────────────────────

    def _collect_chunks(self, repo_path: str):
        """Walk the repo and yield text chunks from code files."""
        base = Path(repo_path)
        skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}

        for file_path in base.rglob("*"):
            if not file_path.is_file():
                continue
            if any(part in skip_dirs for part in file_path.parts):
                continue
            if file_path.suffix not in _CODE_EXTENSIONS:
                continue
            if file_path.stat().st_size > 200_000:  # skip huge files
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                relative = str(file_path.relative_to(base))

                for chunk in self._split_text(content):
                    yield {"file_path": relative, "content": chunk}
            except Exception as exc:
                logger.debug(f"Skipping {file_path}: {exc}")

    def _split_text(self, text: str):
        """Simple sliding-window chunker."""
        text = text.strip()
        if len(text) <= _MAX_CHUNK_CHARS:
            yield text
            return

        start = 0
        while start < len(text):
            end = start + _MAX_CHUNK_CHARS
            yield text[start:end]
            start = end - _CHUNK_OVERLAP

    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts using Gemini."""
        if not settings.GOOGLE_API_KEY:
            # Return zero vectors when API key is missing (dev/test mode)
            return [[0.0] * _EMBEDDING_DIM for _ in texts]
        try:
            results = genai.embed_content(
                model=_EMBEDDING_MODEL,
                content=texts,
                task_type="retrieval_document",
            )
            return results["embedding"] if isinstance(results["embedding"][0], list) else [results["embedding"]]
        except Exception as exc:
            logger.error(f"Embedding failed: {exc}")
            return [[0.0] * _EMBEDDING_DIM for _ in texts]

    async def _ensure_table(self) -> None:
        """Create the rag_chunks table with a vector column if it doesn't exist."""
        await self._db.execute(text("""
            CREATE TABLE IF NOT EXISTS rag_chunks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding vector(768),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        await self._db.execute(text("""
            CREATE INDEX IF NOT EXISTS rag_chunks_session_idx ON rag_chunks(session_id)
        """))
        await self._db.commit()

    async def _insert_chunk(
        self,
        session_id: str,
        file_path: str,
        content: str,
        embedding: list[float],
    ) -> None:
        vector_str = "[" + ",".join(str(v) for v in embedding) + "]"
        await self._db.execute(
            text("""
                INSERT INTO rag_chunks (id, session_id, file_path, content, embedding)
                VALUES (:id, :session_id, :file_path, :content, :embedding::vector)
            """),
            {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "file_path": file_path,
                "content": content,
                "embedding": vector_str,
            },
        )
