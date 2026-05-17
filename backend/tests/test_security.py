"""
Tests for LobsterTrapClient — PII redaction, policy enforcement.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx


class TestLobsterTrapClient:

    @pytest.mark.asyncio
    async def test_redact_pii_calls_lobster_trap(self):
        """Test that redact_pii makes the correct HTTP call."""
        with patch("security.lobster_client.httpx.AsyncClient") as MockClient:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "redacted_content": "Hello [REDACTED-PII], your order is ready."
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

            from security.lobster_client import LobsterTrapClient
            client = LobsterTrapClient()
            result = await client.redact_pii("Hello john.doe@example.com, your order is ready.")

        assert "[REDACTED-PII]" in result

    @pytest.mark.asyncio
    async def test_redact_pii_fallback_in_development(self):
        """Test that PII redaction falls back gracefully in dev mode."""
        with patch("security.lobster_client.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("security.lobster_client.settings") as mock_settings:
                mock_settings.LOBSTER_TRAP_URL = "http://localhost:8080"
                mock_settings.is_development = True

                from security.lobster_client import LobsterTrapClient
                client = LobsterTrapClient()
                original = "This is my email: test@example.com"
                result = await client.redact_pii(original)

        # In dev mode, should return original content without crashing
        assert result == original

    @pytest.mark.asyncio
    async def test_check_policy_deny_for_junior_prod(self):
        """Test that policy check returns DENY for junior accessing production."""
        with patch("security.lobster_client.httpx.AsyncClient") as MockClient:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "event_type": "DENY",
                "severity": "HIGH",
                "rule_triggered": "block_prod_for_junior",
                "action_taken": "blocked",
                "allowed": False,
                "original_intent": "production_access",
                "resource_requested": "production",
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

            from security.lobster_client import LobsterTrapClient
            client = LobsterTrapClient()
            event = await client.check_policy(
                content="access_request:production",
                session={
                    "session_seniority": "junior",
                    "resource_type": "production",
                },
            )

        assert event.event_type == "DENY"
        assert event.allowed is False
        assert event.severity == "HIGH"
        assert event.rule_triggered == "block_prod_for_junior"

    @pytest.mark.asyncio
    async def test_check_policy_dev_fallback_returns_log_event(self):
        """Test that dev fallback returns a LOG event when Lobster Trap is down."""
        with patch("security.lobster_client.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("security.lobster_client.settings") as mock_settings:
                mock_settings.LOBSTER_TRAP_URL = "http://localhost:8080"
                mock_settings.is_development = True

                from security.lobster_client import LobsterTrapClient
                client = LobsterTrapClient()
                event = await client.check_policy("some content", {})

        assert event.event_type == "LOG"
        assert event.allowed is True  # dev fallback allows by default

    @pytest.mark.asyncio
    async def test_check_access_builds_correct_session_context(self):
        """Test that check_access passes the right context to check_policy."""
        from security.lobster_client import LobsterTrapClient
        client = LobsterTrapClient()

        with patch.object(client, "check_policy", new_callable=AsyncMock) as mock_policy:
            from security.lobster_client import LobsterEvent
            mock_policy.return_value = LobsterEvent(
                event_type="LOG",
                severity="LOW",
                rule_triggered="log_all",
                action_taken="logged",
                allowed=True,
            )

            await client.check_access(
                resource="github_repos",
                seniority="junior",
                agent_category="qa",
                session_id="test-session-123",
            )

        call_kwargs = mock_policy.call_args
        assert call_kwargs is not None
        session_ctx = call_kwargs.kwargs.get("session") or call_kwargs.args[1]
        assert session_ctx["session_seniority"] == "junior"
        assert session_ctx["resource_type"] == "github_repos"
        assert session_ctx["agent_category"] == "qa"

    @pytest.mark.asyncio
    async def test_log_event_does_not_raise_on_connection_error(self):
        """Test that log_event is fire-and-forget — never raises."""
        with patch("security.lobster_client.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

            from security.lobster_client import LobsterTrapClient
            client = LobsterTrapClient()
            # Should not raise
            await client.log_event({"event_type": "LOG", "severity": "LOW"})
