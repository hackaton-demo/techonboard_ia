"""
Profile Analyzer — reads GitHub profile and conducts adaptive interview via Gemini Pro.
"""

import json
import logging
import re
from typing import Any, AsyncGenerator

import google.generativeai as genai

from config import get_settings
from company_config_loader import get_company_name, get_team_stack, get_tools_summary
from integrations.github_client import GitHubClient

logger = logging.getLogger(__name__)
settings = get_settings()

INTERVIEW_SYSTEM_PROMPT = """
You are the onboarding agent specialised in {agent_name} for {company_name}.

Your goal is to accomplish two things simultaneously in a single natural conversation:
1. Make the new developer feel welcome and comfortable
2. Detect their real stack, level and gaps to personalise their onboarding

YOUR ROLE KNOWLEDGE:
- Tools they will use: {tools}
- Stack of the team they are joining: {team_stack}
- What they most need to learn for this role: {learning_areas}

CONVERSATION RULES:
- Be warm and professional, not robotic
- Ask at most 6 questions, in this order:
  1. Recent general stack
  2. Whether they know the team's specific stack
  3. Area where they feel most uncertain when joining a new team
  4. Preferred learning style
  5. Expectations for the first 30 days
  6. [Only if you detected a gap in Q2] Estimated time to ramp up on the missing tool

- Adapt each question based on the previous answer
- If the developer proves to be more senior than indicated, adjust your tone accordingly
- If they seem more junior, be more structured and reassuring

WHEN THE INTERVIEW IS OVER, generate a JSON with this exact format:
{{
  "stack_actual": ["list of technologies mentioned"],
  "stack_gaps": ["team tools they don't know"],
  "nivel_real_detectado": "junior|mid|senior",
  "estilo_aprendizaje": "docs|codigo|hands-on|mixto",
  "expectativas": "free text",
  "areas_enfasis": ["areas where the tour should go deeper"],
  "ticket_complexity": "low|medium|high",
  "notas_para_manager": "relevant observations"
}}
"""


class ProfileAnalyzer:
    """Analyzes a developer's GitHub profile and conducts the onboarding interview."""

    def __init__(self) -> None:
        self._github = GitHubClient()
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)

    async def analyze_github_profile(self, username: str) -> dict[str, Any]:
        """Fetch and analyze a developer's GitHub profile."""
        if settings.DEMO_FAST_MODE:
            logger.info("DEMO_FAST_MODE: returning cached profile for %s", username)
            return {
                "username": username,
                "name": username.replace("-", " ").title(),
                "bio": "Full-stack developer joining the team",
                "public_repos": 12,
                "top_languages": ["Python", "TypeScript", "Go"],
                "recent_repos": [{"name": "my-app", "language": "Python", "stars": 2}],
                "company": None,
                "followers": 5,
                "raw_language_counts": {"Python": 8, "TypeScript": 3, "Go": 1},
            }
        try:
            profile = await self._github.get_user_profile(username)
            repos = await self._github.get_user_repos(username)

            # Compute language distribution
            lang_counts: dict[str, int] = {}
            for repo in repos:
                lang = repo.get("language")
                if lang:
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1

            top_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:5]

            return {
                "username": username,
                "name": profile.get("name"),
                "bio": profile.get("bio"),
                "public_repos": profile.get("public_repos", 0),
                "top_languages": [lang for lang, _ in top_langs],
                "recent_repos": profile.get("recent_repos", []),
                "company": profile.get("company"),
                "followers": profile.get("followers", 0),
                "raw_language_counts": dict(top_langs),
            }
        except Exception as exc:
            logger.error(f"GitHub profile analysis failed for {username}: {exc}")
            return {"username": username, "error": str(exc)}

    async def conduct_interview(
        self,
        session_id: str,
        agent_profile: dict[str, Any],
        github_profile: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream interview tokens from Gemini Pro.

        Yields text tokens as they are generated.
        The last yielded chunk will be the JSON result prefixed with __RESULT__
        """
        if not settings.GOOGLE_API_KEY or settings.MOCK_MODE:
            async for token in self._mock_interview(agent_profile):
                yield token
            return

        tools_str = json.dumps(agent_profile.get("tools", {}), ensure_ascii=False)
        learning_areas = "\n".join(
            agent_profile.get("learning_sequence", ["Team stack knowledge"])
        )

        system_prompt = INTERVIEW_SYSTEM_PROMPT.format(
            agent_name=agent_profile.get("name", "Onboarding Agent"),
            company_name=get_company_name(),
            tools=tools_str or get_tools_summary(),
            team_stack=get_team_stack(),
            learning_areas=learning_areas,
        )

        # Build context from GitHub profile if available
        context_msg = ""
        if github_profile and not github_profile.get("error"):
            context_msg = (
                f"Developer context: primarily uses {', '.join(github_profile.get('top_languages', []))}. "
                f"Has {github_profile.get('public_repos', 0)} public repos."
            )

        try:
            model = genai.GenerativeModel(
                "gemini-2.0-flash",
                system_instruction=system_prompt,
            )
            chat = model.start_chat()

            # Initial greeting
            initial_message = (
                f"Hello! Welcome to the onboarding process. "
                f"{context_msg} "
                f"Let's start with a question about your recent experience."
            )

            response = await chat.send_message_async(
                initial_message, stream=True
            )
            async for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as exc:
            logger.error(f"Interview streaming failed (falling back to mock): {exc}")
            async for token in self._mock_interview(agent_profile):
                yield token

    def extract_interview_result(self, full_text: str) -> dict[str, Any]:
        """Extract the JSON result from the full interview text."""
        json_pattern = r'\{[^{}]*"stack_actual"[^{}]*\}'
        match = re.search(json_pattern, full_text, re.DOTALL)

        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Try to find any JSON block
        json_blocks = re.findall(r'\{[\s\S]*?\}', full_text)
        for block in reversed(json_blocks):
            try:
                data = json.loads(block)
                if "stack_actual" in data or "nivel_real_detectado" in data:
                    return data
            except Exception:
                pass

        # Return a default structure if nothing found
        logger.warning(f"Could not extract interview JSON from response")
        return {
            "stack_actual": [],
            "stack_gaps": [],
            "nivel_real_detectado": "mid",
            "estilo_aprendizaje": "mixto",
            "expectativas": "Not extracted from the interview",
            "areas_enfasis": [],
            "ticket_complexity": "medium",
            "notas_para_manager": "Unstructured interview result available",
        }

    async def _mock_interview(
        self, agent_profile: dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Mock interview for development / no API key."""
        import asyncio
        name = agent_profile.get("name", "Developer")

        # Simulate streaming by sending each sentence as a separate token with delay
        messages = [
            f"Hello! Welcome to the team. I'm your onboarding agent for the **{name}** role.\n\n",
            "To personalise your 14-day plan, I have a few quick questions.\n\n",
            "**Question 1:** What technologies have you been working with most recently?\n\n",
            "_In demo mode the interview completes automatically. With a Gemini API key it would be fully interactive._\n\n",
            "**Analysing profile...** Generating your personalised onboarding plan ✓",
        ]

        for msg in messages:
            yield msg
            await asyncio.sleep(0.6)

        result = {
            "stack_actual": ["Python", "React", "PostgreSQL"],
            "stack_gaps": [],
            "nivel_real_detectado": "mid",
            "estilo_aprendizaje": "hands-on",
            "expectativas": "Contribute to the team quickly and learn best practices",
            "areas_enfasis": ["architecture", "testing"],
            "ticket_complexity": "medium",
            "notas_para_manager": "Demo mode — interview not conducted",
        }
        yield f"__RESULT__{json.dumps(result, ensure_ascii=False)}"
