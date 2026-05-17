"""
Ticket Assigner — uses Gemini Flash to select the best first Jira ticket for a new developer.
"""

import json
import logging
from typing import Any

import google.generativeai as genai

from config import get_settings
from integrations.jira_client import JiraClient

logger = logging.getLogger(__name__)
settings = get_settings()


class TicketAssigner:
    """Selects and assigns the ideal first ticket for an onboarding developer."""

    def __init__(self) -> None:
        self._jira = JiraClient()
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)

    async def find_best_ticket(
        self,
        jira_tickets: list[dict[str, Any]],
        seniority: str,
        interview_profile: dict[str, Any],
        ticket_criteria: dict[str, str],
    ) -> dict[str, Any] | None:
        """Use Gemini Flash to select the most appropriate first ticket."""
        if not jira_tickets:
            logger.warning("No tickets available to assign")
            return None

        criteria = ticket_criteria.get(seniority, ticket_criteria.get("mid", ""))

        if not settings.GOOGLE_API_KEY:
            return self._simple_fallback(jira_tickets, seniority)

        try:
            model = genai.GenerativeModel("gemini-2.0-flash-exp")

            tickets_json = json.dumps(jira_tickets, ensure_ascii=False, indent=2)
            profile_json = json.dumps(interview_profile, ensure_ascii=False, indent=2)

            prompt = f"""
You are a tech lead selecting the ideal first ticket for a new developer.

CRITERIA FOR THE FIRST TICKET ({seniority.upper()}):
{criteria}

DEVELOPER PROFILE:
{profile_json}

AVAILABLE TICKETS:
{tickets_json}

Select the most appropriate ticket considering:
1. It fits the complexity criteria for the {seniority} level
2. It matches the developer's stack (or is a good learning opportunity)
3. It is neither too vague nor too complex for a first ticket
4. Prefer tickets labelled "good-first-issue" if available

Reply ONLY with a JSON with this structure:
{{
  "ticket_id": "ID of the selected ticket",
  "reason": "Why this ticket is ideal for this developer",
  "estimated_hours": "estimated hours",
  "learning_opportunity": "what they will learn from this ticket"
}}
"""
            response = await model.generate_content_async(prompt)
            text = response.text.strip()

            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            result = json.loads(text)

            # Find the full ticket data
            ticket_id = result.get("ticket_id")
            matching = next(
                (t for t in jira_tickets if t["id"] == ticket_id), None
            )

            if matching:
                return {**matching, **result}

            logger.warning(f"Selected ticket {ticket_id} not found in list — using fallback")

        except Exception as exc:
            logger.error(f"Ticket selection with Gemini failed: {exc}")

        return self._simple_fallback(jira_tickets, seniority)

    async def assign_ticket(self, ticket_id: str, dev_username: str) -> bool:
        """Assign a Jira ticket to the developer."""
        try:
            result = await self._jira.assign_ticket(ticket_id, dev_username)
            if result:
                logger.info(f"Ticket {ticket_id} assigned to {dev_username}")
            return result
        except Exception as exc:
            logger.error(f"Failed to assign ticket {ticket_id}: {exc}")
            return False

    def _simple_fallback(
        self, tickets: list[dict[str, Any]], seniority: str
    ) -> dict[str, Any] | None:
        """Select the first good-first-issue or the first ticket if none found."""
        # Prefer good-first-issue labeled tickets for junior
        if seniority == "junior":
            for ticket in tickets:
                if "good-first-issue" in ticket.get("labels", []):
                    return {**ticket, "reason": "Selected by good-first-issue label"}

        # For other levels, pick by story points if available
        sorted_tickets = sorted(
            tickets,
            key=lambda t: t.get("story_points") or 3,
        )

        if seniority in ("senior", "staff", "lead"):
            # Higher complexity
            sorted_tickets = sorted_tickets[-3:] if len(sorted_tickets) >= 3 else sorted_tickets

        return {
            **(sorted_tickets[0] if sorted_tickets else {}),
            "reason": "Selected automatically (Gemini not available)",
        } if sorted_tickets else None
