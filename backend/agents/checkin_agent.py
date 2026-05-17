"""
Check-in Agent — generates personalized check-in messages at days 3, 7 and 14.
"""

import logging
from typing import Any

import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import get_settings
from integrations.slack_client import SlackClient

logger = logging.getLogger(__name__)
settings = get_settings()


class CheckinAgent:
    """Generates and delivers scheduled check-in messages for onboarding sessions."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._slack = SlackClient()
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)

    async def run_checkin(self, session_id: str, day: int) -> str:
        """Generate a personalized check-in message for the given day."""
        from models.onboarding import OnboardingSession

        try:
            result = await self._db.execute(
                select(OnboardingSession).where(OnboardingSession.id == session_id)
            )
            session = result.scalar_one_or_none()
        except Exception as exc:
            logger.error(f"Failed to fetch session {session_id}: {exc}")
            return self._default_message(session_id, day)

        if not session:
            logger.warning(f"Session {session_id} not found for day {day} check-in")
            return self._default_message(session_id, day)

        interview_profile = session.interview_profile or {}
        onboarding_plan = session.onboarding_plan or {}
        username = session.dev_github_username
        assigned_ticket = session.assigned_ticket_id

        if not settings.GOOGLE_API_KEY:
            return self._default_message(username, day)

        try:
            model = genai.GenerativeModel("gemini-2.0-flash")

            prompt = f"""
You are the TechOnboard onboarding agent generating a check-in for day {day}.

DEVELOPER: {username}
DAY: {day}
ASSIGNED TICKET: {assigned_ticket or "Not assigned yet"}
PROFILE: {interview_profile}

Generate a check-in message in English that:
1. Is warm and specific (not generic)
2. Asks about progress on the ticket
3. Offers help if there are blockers
4. Adapts the tone to the day ({day}):
   - Day 3: very close, asks if they found everything they need
   - Day 7: more focused on the ticket and the team
   - Day 14: more reflective, asks what they learned and what they would improve in the process

Maximum 3 short paragraphs. Professional but human tone.
"""
            response = await model.generate_content_async(prompt)
            message = response.text.strip()
            logger.info(f"Check-in day {day} generated for session {session_id}")
            return message

        except Exception as exc:
            logger.error(f"Check-in generation failed: {exc}")
            return self._default_message(username, day)

    async def send_checkin_slack(
        self, session_id: str, day: int, message: str
    ) -> bool:
        """Send the check-in message to the developer's Slack channel."""
        from models.onboarding import OnboardingSession

        try:
            result = await self._db.execute(
                select(OnboardingSession).where(OnboardingSession.id == session_id)
            )
            session = result.scalar_one_or_none()
        except Exception as exc:
            logger.error(f"Failed to fetch session for Slack: {exc}")
            return False

        if not session:
            return False

        channel = "#general"
        try:
            agent_profile = session.agent_profile
            if agent_profile and agent_profile.access_rules:
                seniority_rules = agent_profile.access_rules.get(session.seniority, {})
                channels = seniority_rules.get("slack_channels", [])
                if channels:
                    channel = channels[0]
        except Exception:
            pass

        return await self._slack.send_checkin_message(
            channel=channel,
            username=session.dev_github_username,
            message=message,
        )

    def _default_message(self, username: str | None, day: int) -> str:
        messages = {
            3: (
                f"Hey {username or 'Developer'}! It's been 3 days since you joined the team. "
                "How are you getting on with the environment setup? Did you find everything you needed? "
                "If you have any questions or blockers, don't hesitate to mention them — we're here to help."
            ),
            7: (
                f"Hey {username or 'Developer'}! You've been with us for a week now. "
                "How is the first ticket going? Were you able to connect with teammates? "
                "If you need more codebase context or have questions about the process, just let us know."
            ),
            14: (
                f"Hey {username or 'Developer'}! You've been on the team for 2 weeks — an important milestone. "
                "What helped you most during the onboarding? What would you improve? "
                "Your feedback helps us improve the process for the next developer who joins."
            ),
        }
        return messages.get(day, f"Day {day} check-in for {username or 'Developer'}.")
