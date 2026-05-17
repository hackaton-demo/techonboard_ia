import logging
from typing import Any

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SlackClient:
    """Thin wrapper around slack-sdk for TechOnboard notifications."""

    def __init__(self) -> None:
        self._client = None
        self._connect()

    def _connect(self) -> None:
        if not settings.SLACK_BOT_TOKEN:
            logger.warning("SLACK_BOT_TOKEN not set — Slack features will be mocked")
            return
        try:
            from slack_sdk.web.async_client import AsyncWebClient
            self._client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
            logger.info("Slack client initialised")
        except Exception as exc:
            logger.error(f"Failed to initialise Slack client: {exc}")

    async def invite_to_channel(self, user_email: str, channel: str) -> bool:
        """Invite a user (by email) to a Slack channel."""
        if not self._client:
            logger.info(f"Mock: invited {user_email} to {channel}")
            return True
        try:
            # Look up user by email first
            result = await self._client.users_lookupByEmail(email=user_email)
            user_id = result["user"]["id"]

            await self._client.conversations_invite(
                channel=channel,
                users=user_id,
            )
            logger.info(f"Invited {user_email} to Slack channel {channel}")
            return True
        except Exception as exc:
            logger.error(f"Failed to invite {user_email} to {channel}: {exc}")
            return False

    async def send_onboarding_message(
        self,
        channel: str,
        username: str,
        plan_summary: str,
    ) -> bool:
        """Send the welcome + onboarding plan summary to a Slack channel."""
        message = (
            f":wave: *Welcome to the team, {username}!* :tada:\n\n"
            f"Your personalised onboarding plan is ready. Here's a quick summary:\n\n"
            f"{plan_summary}\n\n"
            f"Your first ticket has been assigned in Jira. "
            f"Reach out to your buddy if you have any questions — we're here to help!"
        )

        return await self._send_message(channel, message)

    async def send_checkin_message(
        self, channel: str, username: str, message: str
    ) -> bool:
        """Send a check-in message to a Slack channel."""
        full_message = f"*Check-in for {username}*\n\n{message}"
        return await self._send_message(channel, full_message)

    async def _send_message(self, channel: str, text: str) -> bool:
        if not self._client:
            logger.info(f"Mock Slack message to {channel}:\n{text[:100]}...")
            return True
        try:
            await self._client.chat_postMessage(
                channel=channel,
                text=text,
                unfurl_links=False,
            )
            logger.info(f"Sent Slack message to {channel}")
            return True
        except Exception as exc:
            logger.error(f"Failed to send Slack message to {channel}: {exc}")
            return False
