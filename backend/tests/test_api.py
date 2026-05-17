"""
Integration tests for the FastAPI endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def app():
    """Create a test app instance with mocked dependencies."""
    with patch("models.database.init_db", new_callable=AsyncMock):
        with patch("catalog.agent_profiles.seed_agents_to_db", new_callable=AsyncMock):
            from main import create_app
            return create_app()


@pytest.fixture
async def client(app):
    """Async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


class TestHealth:

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test the health endpoint returns 200."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "techonboard-backend"

    @pytest.mark.asyncio
    async def test_health_check_has_environment(self, client):
        """Test the health endpoint includes environment field."""
        response = await client.get("/health")
        data = response.json()
        assert "environment" in data


class TestAgentsAPI:

    @pytest.mark.asyncio
    async def test_list_agents_returns_200(self, client):
        """Test that GET /api/v1/agents returns 200."""
        with patch("api.agents.get_db") as mock_get_db:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_get_db.return_value.__aexit__ = AsyncMock(return_value=None)

            # Patch the Depends injection
            from fastapi import FastAPI
            from models.database import get_db
            from sqlalchemy.ext.asyncio import AsyncSession

            async def override_db():
                yield mock_session

            client.app.dependency_overrides[get_db] = override_db

            response = await client.get("/api/v1/agents")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, client):
        """Test that GET /api/v1/agents/{id} returns 404 for unknown agent."""
        from models.database import get_db
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        async def override_db():
            yield mock_session

        client.app.dependency_overrides[get_db] = override_db

        response = await client.get("/api/v1/agents/qa-engineer-nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_default_agent_forbidden(self, client):
        """Test that deleting a default agent returns 403."""
        import uuid
        from models.database import get_db
        from models.agent_profile import AgentProfile

        mock_agent = MagicMock(spec=AgentProfile)
        mock_agent.id = uuid.uuid4()
        mock_agent.is_custom = False  # Default agent

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_agent
        mock_session.execute = AsyncMock(return_value=mock_result)

        async def override_db():
            yield mock_session

        client.app.dependency_overrides[get_db] = override_db

        agent_id = str(mock_agent.id)
        response = await client.delete(f"/api/v1/agents/{agent_id}")
        assert response.status_code == 403


class TestPaymentsAPI:

    @pytest.mark.asyncio
    async def test_activate_agent_returns_402(self, client):
        """Test that POST /api/v1/activate-agent returns HTTP 402."""
        response = await client.post(
            "/api/v1/activate-agent",
            json={
                "agent_id": "qa-engineer",
                "seniority": "junior",
                "dev_email": "dev@example.com",
                "dev_github_username": "devuser",
                "project_repo_url": "https://github.com/demo/repo",
            },
        )
        assert response.status_code == 402
        data = response.json()
        assert "payment_url" in data
        assert "amount" in data
        assert "wallet_address" in data

    @pytest.mark.asyncio
    async def test_payment_verification_invalid_tx_hash(self, client):
        """Test that an invalid tx_hash returns 402."""
        from models.database import get_db

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        async def override_db():
            yield mock_session

        client.app.dependency_overrides[get_db] = override_db

        with patch("payments.x402_handler.x402PaymentHandler.verify_payment", new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = False

            response = await client.post(
                "/api/v1/activate-agent/verify",
                json={
                    "tx_hash": "invalid_hash_xyz",
                    "agent_id": "qa-engineer",
                    "seniority": "junior",
                    "dev_email": "dev@example.com",
                    "dev_github_username": "devuser",
                    "project_repo_url": "https://github.com/demo/repo",
                },
            )
        assert response.status_code == 402

    @pytest.mark.asyncio
    async def test_demo_payment_succeeds(self, client):
        """Test that a demo_ tx_hash is accepted and creates a session."""
        import uuid
        from models.database import get_db
        from models.agent_profile import AgentProfile

        mock_agent = MagicMock(spec=AgentProfile)
        mock_agent.id = uuid.uuid4()
        mock_agent.slug = "qa-engineer"

        mock_session_obj = MagicMock()
        mock_session_obj.id = uuid.uuid4()
        mock_session_obj.status = "interviewing"

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_agent
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        # Make refresh set the session attributes
        async def mock_refresh(obj):
            obj.id = mock_session_obj.id
            obj.status = "interviewing"

        mock_db.refresh = mock_refresh

        async def override_db():
            yield mock_db

        client.app.dependency_overrides[get_db] = override_db

        response = await client.post(
            "/api/v1/activate-agent/verify",
            json={
                "tx_hash": "demo_hackathon_2026",
                "agent_id": "qa-engineer",
                "seniority": "junior",
                "dev_email": "dev@example.com",
                "dev_github_username": "devuser",
                "project_repo_url": "https://github.com/demo/repo",
            },
        )
        # Should succeed with 200
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "interviewing"
