import logging
from typing import Any

import google.generativeai as genai

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_PROMPT_TEMPLATE = """
You are an expert at writing system prompts for AI onboarding agents.

Generate a comprehensive system_prompt_template for an AI onboarding agent with the following profile:

Agent Name: {agent_name}
Category: {category}
Seniority Levels: {seniority_levels}
Tools the agent knows about: {tools}
Team Stack: {team_stack}
Company Name: {company_name}

The system prompt template should:
1. Define the agent's persona and role
2. List the specific tools and technologies it knows about
3. Specify the interview flow (6 questions max, adaptive)
4. Include the required JSON output format at the end of the interview
5. Use {{company_name}}, {{team_stack}}, {{seniority}}, {{tools}} as template variables

The JSON output format must always include:
- stack_actual: list of technologies the candidate mentioned
- stack_gaps: tools the team uses that the candidate doesn't know
- nivel_real_detectado: junior|mid|senior|lead|staff
- estilo_aprendizaje: docs|codigo|hands-on|mixto
- expectativas: free text
- areas_enfasis: list of areas where the tour should go deeper
- ticket_complexity: low|medium|high
- notas_para_manager: relevant observations

Write ONLY the system prompt text, no explanations.
"""


async def generate_system_prompt(
    agent_data: dict[str, Any],
    team_stack: str,
    company_name: str,
) -> str:
    """Use Gemini Pro to generate a system_prompt_template for a custom agent.

    Falls back to a sensible default if Gemini is unavailable.
    """
    if not settings.GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not set — using default system prompt template")
        return _build_fallback_prompt(agent_data, team_stack, company_name)

    try:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        filled_prompt = _PROMPT_TEMPLATE.format(
            agent_name=agent_data.get("name", "Custom Agent"),
            category=agent_data.get("category", "dev"),
            seniority_levels=", ".join(agent_data.get("seniority_levels", ["mid"])),
            tools=str(agent_data.get("tools", {})),
            team_stack=team_stack,
            company_name=company_name,
        )

        response = await model.generate_content_async(filled_prompt)
        generated = response.text.strip()

        if generated:
            logger.info(f"Generated system prompt for agent '{agent_data.get('name')}'")
            return generated

    except Exception as exc:
        logger.error(f"Gemini prompt generation failed: {exc}")

    return _build_fallback_prompt(agent_data, team_stack, company_name)


def _build_fallback_prompt(
    agent_data: dict[str, Any],
    team_stack: str,
    company_name: str,
) -> str:
    """Build a minimal but functional system prompt without Gemini."""
    name = agent_data.get("name", "Custom Agent")
    category = agent_data.get("category", "dev")
    tools_str = str(agent_data.get("tools", {}))

    return (
        f"You are the onboarding agent specialised in {name} for {{company_name}}.\n\n"
        f"Category: {category}\n"
        f"Team tools: {tools_str}\n"
        f"Main stack: {{team_stack}}\n"
        f"Expected level: {{seniority}}\n\n"
        "Conduct a warm and professional interview with at most 6 adaptive questions.\n"
        "Detect the candidate's real stack, gaps and learning style.\n\n"
        "When finished, generate a JSON with: stack_actual, stack_gaps, nivel_real_detectado, "
        "estilo_aprendizaje, expectativas, areas_enfasis, ticket_complexity, notas_para_manager."
    )
