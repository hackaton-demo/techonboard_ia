"""
Access Provisioner — provisions GitHub, Jira, and Slack access for a new developer.
Each access grant is checked through Lobster Trap before execution.
"""

import logging
from typing import Any

from config import get_settings
from integrations.github_client import GitHubClient
from integrations.jira_client import JiraClient
from integrations.slack_client import SlackClient
from security.lobster_client import LobsterTrapClient

logger = logging.getLogger(__name__)
settings = get_settings()


class AccessProvisioner:
    """Provisions all required accesses for a developer session."""

    def __init__(self) -> None:
        self._github = GitHubClient()
        self._jira = JiraClient()
        self._slack = SlackClient()
        self._lobster = LobsterTrapClient()

    async def provision_all(
        self,
        session: Any,  # OnboardingSession model instance
        agent_profile: dict[str, Any],
    ) -> dict[str, Any]:
        """Provision all accesses defined in the agent's access_rules for the session's seniority.

        Returns a dict mapping resource -> status: "granted" | "requires_approval" | "blocked"
        """
        seniority = session.seniority
        access_rules: dict[str, Any] = agent_profile.get("access_rules", {})
        rules_for_level = access_rules.get(seniority, {})

        if not rules_for_level:
            logger.warning(
                f"No access rules for seniority '{seniority}' in agent '{agent_profile.get('name')}'"
            )
            return {}

        status: dict[str, Any] = {}

        for resource, policy in rules_for_level.items():
            if isinstance(policy, bool):
                # Boolean flags like "code_review_required" are not resources to provision
                status[resource] = "info"
                continue

            result = await self._provision_resource(
                resource=resource,
                policy=policy,
                session=session,
                agent_profile=agent_profile,
            )
            status[resource] = result

        return status

    async def _provision_resource(
        self,
        resource: str,
        policy: str,
        session: Any,
        agent_profile: dict[str, Any],
    ) -> str:
        """
        Provision a single resource after checking with Lobster Trap.
        policy: "auto" | "requires_approval" | "blocked"
        """
        # First, check with Lobster Trap
        lobster_event = await self._lobster.check_access(
            resource=resource,
            seniority=session.seniority,
            agent_category=agent_profile.get("category", "dev"),
            session_id=str(session.id),
        )

        # If Lobster Trap denies, immediately block regardless of policy
        if not lobster_event.allowed:
            logger.info(
                f"Lobster Trap DENIED access to '{resource}' for session {session.id} "
                f"(rule: {lobster_event.rule_triggered})"
            )
            return "blocked"

        if policy == "blocked":
            return "blocked"

        if policy == "requires_approval":
            # Log the pending approval
            logger.info(f"Access to '{resource}' requires manager approval for session {session.id}")
            return "requires_approval"

        if policy == "auto":
            # Actually provision
            granted = await self._execute_provision(
                resource=resource,
                session=session,
                agent_profile=agent_profile,
            )
            return "granted" if granted else "failed"

        return "unknown"

    async def _execute_provision(
        self,
        resource: str,
        session: Any,
        agent_profile: dict[str, Any],
    ) -> bool:
        """Execute the actual provisioning action for a resource."""
        username = session.dev_github_username
        email = session.dev_email

        try:
            # GitHub access
            if "github" in resource:
                if "org" in resource:
                    return await self._github.invite_to_org(username)
                # For repo-specific resources, use the project repo
                repo_name = session.project_repo_url.split("/")[-1] if session.project_repo_url else "demo-repo"
                permission = "push" if "write" in resource else "pull"
                return await self._github.invite_to_repo(username, repo_name, permission)

            # Jira access (we just log it — Jira access is managed via project settings)
            if "jira" in resource:
                logger.info(f"Jira access '{resource}' provisioned for {username} (via project settings)")
                return True

            # Slack channel invitations
            if "slack" in resource or resource.startswith("#"):
                channels: list = []
                if isinstance(agent_profile.get("access_rules", {}).get(session.seniority, {}).get("slack_channels"), list):
                    channels = agent_profile["access_rules"][session.seniority]["slack_channels"]
                for channel in channels:
                    await self._slack.invite_to_channel(email, channel)
                return True

            # For other resources (staging_env, browserstack, etc.) — log as provisioned
            logger.info(
                f"Resource '{resource}' provisioned for {username} "
                f"(external system — manual step or automated via IaC)"
            )
            return True

        except Exception as exc:
            logger.error(f"Failed to provision '{resource}' for {username}: {exc}")
            return False
