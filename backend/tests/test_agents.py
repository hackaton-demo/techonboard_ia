"""
Tests for ProfileAnalyzer and TicketAssigner.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── ProfileAnalyzer tests ─────────────────────────────────────────────────────

class TestProfileAnalyzer:

    @pytest.mark.asyncio
    async def test_analyze_github_profile_success(self):
        """Test that GitHub profile analysis returns expected structure."""
        with patch("agents.profile_analyzer.GitHubClient") as MockGH:
            mock_client = MagicMock()
            MockGH.return_value = mock_client
            mock_client.get_user_profile = AsyncMock(
                return_value={
                    "username": "testuser",
                    "name": "Test User",
                    "bio": "Python developer",
                    "public_repos": 25,
                    "top_languages": {"Python": 10, "TypeScript": 5},
                    "recent_repos": [],
                    "company": "Acme Corp",
                    "followers": 100,
                }
            )
            mock_client.get_user_repos = AsyncMock(
                return_value=[
                    {"name": "repo1", "language": "Python"},
                    {"name": "repo2", "language": "TypeScript"},
                ]
            )

            from agents.profile_analyzer import ProfileAnalyzer
            analyzer = ProfileAnalyzer()
            result = await analyzer.analyze_github_profile("testuser")

        assert result["username"] == "testuser"
        assert "top_languages" in result
        assert result["public_repos"] == 25

    @pytest.mark.asyncio
    async def test_analyze_github_profile_error_returns_partial(self):
        """Test that GitHub errors don't crash — returns partial result."""
        with patch("agents.profile_analyzer.GitHubClient") as MockGH:
            mock_client = MagicMock()
            MockGH.return_value = mock_client
            mock_client.get_user_profile = AsyncMock(
                side_effect=Exception("GitHub API unavailable")
            )
            mock_client.get_user_repos = AsyncMock(return_value=[])

            from agents.profile_analyzer import ProfileAnalyzer
            analyzer = ProfileAnalyzer()
            result = await analyzer.analyze_github_profile("testuser")

        assert result["username"] == "testuser"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_mock_interview_streams_tokens(self):
        """Test that mock interview yields tokens when no API key is set."""
        with patch("agents.profile_analyzer.settings") as mock_settings:
            mock_settings.GOOGLE_API_KEY = ""

            from agents.profile_analyzer import ProfileAnalyzer
            analyzer = ProfileAnalyzer()
            agent_profile = {"name": "QA Engineer", "tools": {}, "learning_sequence": []}

            tokens = []
            async for token in analyzer.conduct_interview(
                session_id="test-session",
                agent_profile=agent_profile,
            ):
                tokens.append(token)

        assert len(tokens) > 0
        # Last token should contain the result JSON
        last_token = tokens[-1]
        assert "__RESULT__" in last_token

    def test_extract_interview_result_valid_json(self):
        """Test extraction of JSON from interview text."""
        from agents.profile_analyzer import ProfileAnalyzer
        analyzer = ProfileAnalyzer()

        sample_text = """
        Gracias por las respuestas.

        {"stack_actual": ["Python", "FastAPI"], "stack_gaps": ["Playwright"],
        "nivel_real_detectado": "mid", "estilo_aprendizaje": "hands-on",
        "expectativas": "Contribuir en el primer sprint", "areas_enfasis": ["testing"],
        "ticket_complexity": "medium", "notas_para_manager": "Dev prometedor"}
        """
        result = analyzer.extract_interview_result(sample_text)

        assert result["nivel_real_detectado"] == "mid"
        assert "Python" in result["stack_actual"]
        assert result["ticket_complexity"] == "medium"

    def test_extract_interview_result_fallback(self):
        """Test fallback when no JSON is found."""
        from agents.profile_analyzer import ProfileAnalyzer
        analyzer = ProfileAnalyzer()

        result = analyzer.extract_interview_result("No JSON here at all.")
        assert "nivel_real_detectado" in result
        assert "ticket_complexity" in result


# ── TicketAssigner tests ──────────────────────────────────────────────────────

class TestTicketAssigner:

    SAMPLE_TICKETS = [
        {
            "id": "DEMO-101",
            "summary": "Add input validation",
            "description": "Add Pydantic validators",
            "issue_type": "Task",
            "priority": "Medium",
            "labels": ["backend", "good-first-issue"],
            "story_points": 3,
            "components": ["API"],
        },
        {
            "id": "DEMO-102",
            "summary": "Refactor auth module",
            "description": "Large refactoring task",
            "issue_type": "Task",
            "priority": "High",
            "labels": ["backend"],
            "story_points": 8,
            "components": ["Auth"],
        },
    ]

    def test_simple_fallback_junior_prefers_good_first_issue(self):
        """Test that junior level gets good-first-issue tickets."""
        from agents.ticket_assigner import TicketAssigner
        assigner = TicketAssigner()

        result = assigner._simple_fallback(self.SAMPLE_TICKETS, "junior")

        assert result is not None
        assert result["id"] == "DEMO-101"

    def test_simple_fallback_returns_none_for_empty_list(self):
        """Test that empty ticket list returns None."""
        from agents.ticket_assigner import TicketAssigner
        assigner = TicketAssigner()

        result = assigner._simple_fallback([], "junior")
        assert result is None

    @pytest.mark.asyncio
    async def test_find_best_ticket_returns_fallback_without_api_key(self):
        """Test that find_best_ticket falls back gracefully without Gemini."""
        with patch("agents.ticket_assigner.settings") as mock_settings:
            mock_settings.GOOGLE_API_KEY = ""

            from agents.ticket_assigner import TicketAssigner
            assigner = TicketAssigner()

            result = await assigner.find_best_ticket(
                jira_tickets=self.SAMPLE_TICKETS,
                seniority="junior",
                interview_profile={"stack_actual": ["Python"]},
                ticket_criteria={"junior": "Simple task"},
            )

        assert result is not None
        assert "id" in result

    @pytest.mark.asyncio
    async def test_find_best_ticket_empty_list_returns_none(self):
        """Test that empty ticket list returns None."""
        from agents.ticket_assigner import TicketAssigner
        assigner = TicketAssigner()

        result = await assigner.find_best_ticket(
            jira_tickets=[],
            seniority="mid",
            interview_profile={},
            ticket_criteria={},
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_assign_ticket_calls_jira(self):
        """Test that assign_ticket calls the Jira client."""
        with patch("agents.ticket_assigner.JiraClient") as MockJira:
            mock_jira = MagicMock()
            MockJira.return_value = mock_jira
            mock_jira.assign_ticket = AsyncMock(return_value=True)

            from agents.ticket_assigner import TicketAssigner
            assigner = TicketAssigner()
            assigner._jira = mock_jira

            result = await assigner.assign_ticket("DEMO-101", "developer1")

        assert result is True
        mock_jira.assign_ticket.assert_called_once_with("DEMO-101", "developer1")
