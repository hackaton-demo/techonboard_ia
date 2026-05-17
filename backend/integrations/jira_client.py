import logging
from typing import Any

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class JiraClient:
    """Thin wrapper around atlassian-python-api Jira client."""

    def __init__(self) -> None:
        self._jira = None
        self._connect()

    def _connect(self) -> None:
        if not (settings.JIRA_URL and settings.JIRA_EMAIL and settings.JIRA_API_TOKEN):
            logger.warning("Jira credentials not configured — Jira features will be mocked")
            return
        try:
            from atlassian import Jira
            self._jira = Jira(
                url=settings.JIRA_URL,
                username=settings.JIRA_EMAIL,
                password=settings.JIRA_API_TOKEN,
                cloud=True,
            )
            logger.info(f"Connected to Jira: {settings.JIRA_URL}")
        except Exception as exc:
            logger.error(f"Failed to connect to Jira: {exc}")

    async def get_backlog_tickets(
        self, project_key: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Fetch unassigned tickets from the project backlog."""
        if not self._jira:
            return self._mock_tickets(project_key)
        try:
            jql = (
                f"project = {project_key} "
                f"AND status = 'To Do' "
                f"AND assignee is EMPTY "
                f"ORDER BY created DESC"
            )
            issues = self._jira.jql(jql, limit=limit)
            return [
                {
                    "id": issue["key"],
                    "summary": issue["fields"]["summary"],
                    "description": (issue["fields"].get("description") or ""),
                    "issue_type": issue["fields"]["issuetype"]["name"],
                    "priority": issue["fields"].get("priority", {}).get("name", "Medium"),
                    "labels": issue["fields"].get("labels", []),
                    "story_points": issue["fields"].get("story_points"),
                    "components": [
                        c["name"] for c in issue["fields"].get("components", [])
                    ],
                }
                for issue in issues.get("issues", [])
            ]
        except Exception as exc:
            logger.error(f"Failed to fetch Jira backlog for {project_key}: {exc}")
            return self._mock_tickets(project_key)

    async def assign_ticket(self, ticket_id: str, username: str) -> bool:
        """Assign a Jira ticket to a user."""
        if not self._jira:
            logger.info(f"Mock: assigned {ticket_id} to {username}")
            return True
        try:
            self._jira.assign_issue(ticket_id, username)
            logger.info(f"Assigned {ticket_id} to {username}")
            return True
        except Exception as exc:
            logger.error(f"Failed to assign {ticket_id} to {username}: {exc}")
            return False

    async def create_ticket(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
    ) -> dict[str, Any]:
        """Create a new Jira issue."""
        if not self._jira:
            mock_id = f"{project_key}-MOCK-001"
            logger.info(f"Mock: created ticket {mock_id}: {summary}")
            return {"id": mock_id, "summary": summary}
        try:
            issue = self._jira.create_issue(
                fields={
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": issue_type},
                }
            )
            logger.info(f"Created Jira issue {issue['key']}: {summary}")
            return {"id": issue["key"], "summary": summary}
        except Exception as exc:
            logger.error(f"Failed to create Jira issue in {project_key}: {exc}")
            return {"id": None, "error": str(exc)}

    # ── Demo / fallback data ──────────────────────────────────────────────────

    def _mock_tickets(self, project_key: str) -> list[dict[str, Any]]:
        """Return demo tickets when Jira is not configured."""
        return [
            {
                "id": f"{project_key}-101",
                "summary": "Add input validation to user registration endpoint",
                "description": "The /api/users POST endpoint is missing validation for email format and password strength. Add Pydantic validators and unit tests.",
                "issue_type": "Task",
                "priority": "Medium",
                "labels": ["backend", "validation", "good-first-issue"],
                "story_points": 3,
                "components": ["API"],
            },
            {
                "id": f"{project_key}-102",
                "summary": "Write E2E test for checkout happy path",
                "description": "We need a Playwright test covering the full checkout flow: add to cart → payment → confirmation.",
                "issue_type": "Task",
                "priority": "High",
                "labels": ["qa", "e2e", "playwright"],
                "story_points": 5,
                "components": ["Testing"],
            },
            {
                "id": f"{project_key}-103",
                "summary": "Add Datadog alert for API p99 latency",
                "description": "Create a Datadog monitor that alerts when p99 API response time exceeds 2s over a 5-minute window.",
                "issue_type": "Task",
                "priority": "Medium",
                "labels": ["observability", "devops"],
                "story_points": 3,
                "components": ["Infrastructure"],
            },
            {
                "id": f"{project_key}-104",
                "summary": "Implement responsive mobile variant for ProductCard component",
                "description": "The ProductCard needs a mobile-optimized layout. Figma link attached. Write snapshot test.",
                "issue_type": "Task",
                "priority": "Medium",
                "labels": ["frontend", "mobile", "design-system"],
                "story_points": 3,
                "components": ["Frontend"],
            },
            {
                "id": f"{project_key}-105",
                "summary": "Add dbt not_null tests to orders staging model",
                "description": "The stg_orders model is missing data quality tests. Add not_null and unique tests for order_id and customer_id.",
                "issue_type": "Task",
                "priority": "Low",
                "labels": ["data", "dbt", "data-quality", "good-first-issue"],
                "story_points": 2,
                "components": ["Data"],
            },
        ]
