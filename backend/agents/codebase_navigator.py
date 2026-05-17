"""
Codebase Navigator — indexes a git repo with RAG and generates a personalized tour.
"""

import logging
import shutil
import tempfile
from typing import Any

import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from rag.indexer import RAGIndexer
from rag.retriever import RAGRetriever

logger = logging.getLogger(__name__)
settings = get_settings()


class CodebaseNavigator:
    """Generates a personalized codebase tour using RAG."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._indexer = RAGIndexer(db)
        self._retriever = RAGRetriever(db)
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)

    async def index_repository(self, repo_url: str, session_id: str) -> None:
        """Clone the repository and index it for RAG retrieval."""
        tmp_dir = tempfile.mkdtemp(prefix="techonboard_nav_")
        try:
            repo_path = await self._indexer.clone_repository(repo_url, tmp_dir)
            count = await self._indexer.index_repository(repo_path, session_id)
            logger.info(f"Indexed {count} chunks for session {session_id} from {repo_url}")
        except Exception as exc:
            logger.error(f"Failed to index repository {repo_url}: {exc}")
        finally:
            # Clean up the cloned directory
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

    async def generate_tour(
        self,
        learning_sequence: list[str],
        session_context: dict[str, Any],
    ) -> str:
        """Generate a personalized codebase tour based on the learning sequence and RAG context."""
        session_id = session_context.get("session_id", "")
        seniority = session_context.get("seniority", "mid")
        interview_profile = session_context.get("interview_profile", {})

        # Gather RAG context for each learning topic
        context_chunks: list[str] = []
        for topic in learning_sequence[:6]:
            chunks = await self._retriever.search(
                query=topic,
                session_id=session_id,
                top_k=3,
            )
            for chunk in chunks:
                context_chunks.append(
                    f"### {chunk['file_path']}\n{chunk['content'][:500]}"
                )

        context_text = "\n\n".join(context_chunks[:12])  # limit context size

        if not settings.GOOGLE_API_KEY:
            return self._mock_tour(learning_sequence, seniority)

        try:
            model = genai.GenerativeModel(
                "gemini-2.0-flash-exp",
                generation_config=genai.GenerationConfig(max_output_tokens=600),
            )
            prompt = f"""
You are a senior engineer generating the personalised codebase tour for a new {seniority} developer.

LEARNING SEQUENCE:
{chr(10).join(f"- {topic}" for topic in learning_sequence)}

CODEBASE CONTEXT (relevant repo snippets):
{context_text if context_text else "No indexed context available yet."}

DEVELOPER PROFILE:
- Current stack: {interview_profile.get("stack_actual", [])}
- Detected gaps: {interview_profile.get("stack_gaps", [])}
- Learning style: {interview_profile.get("estilo_aprendizaje", "mixed")}
- Emphasis areas: {interview_profile.get("areas_enfasis", [])}

Generate a codebase tour in markdown format that:
1. Covers each point in the learning sequence
2. Is specific to the real repo code when available
3. Adapts the level of detail to the seniority ({seniority})
4. Includes the exact commands to run the project
5. Highlights the most important files in each area
6. Is motivating and welcoming, not overwhelming
"""

            response = await model.generate_content_async(prompt)
            return response.text.strip()

        except Exception as exc:
            logger.error(f"Tour generation failed: {exc}")
            return self._mock_tour(learning_sequence, seniority)

    def _mock_tour(self, learning_sequence: list[str], seniority: str) -> str:
        """Generate a mock tour for development mode."""
        sections = "\n\n".join(
            f"## {i+1}. {topic}\n\nThis section will be generated with RAG over your real codebase."
            for i, topic in enumerate(learning_sequence)
        )
        return f"""# Codebase Tour — {seniority.capitalize()} Level

Welcome to the team! This is your personalised codebase tour.

{sections}

---
*This tour was generated in demo mode. With the real codebase indexed, each section will include specific code snippets from your repository.*
"""
