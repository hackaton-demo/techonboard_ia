from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Gemini / Google AI
    GOOGLE_API_KEY: str = ""

    # Lobster Trap proxy
    LOBSTER_TRAP_URL: str = "http://lobster-trap:8080"
    LOBSTER_TRAP_POLICY_DIR: str = "./backend/security/policies"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://techonboard:password@db:5432/techonboard"

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"

    # GitHub
    GITHUB_TOKEN: str = ""
    GITHUB_ORG: str = "demo-org"

    # Jira
    JIRA_URL: str = "https://demo.atlassian.net"
    JIRA_EMAIL: str = ""
    JIRA_API_TOKEN: str = ""

    # Slack
    SLACK_BOT_TOKEN: str = ""
    SLACK_WORKSPACE_ID: str = ""

    # x402 Payments
    X402_WALLET_ADDRESS: str = "0xDemoWalletAddress"
    X402_PRICE_JUNIOR: float = 0.50
    X402_PRICE_MID_SENIOR: float = 1.00
    X402_PRICE_STAFF: float = 2.00
    # Base Sepolia testnet; swap to eip155:8453 for Base mainnet
    X402_NETWORK: str = "eip155:84532"
    X402_FACILITATOR_URL: str = "https://x402.org/facilitator"

    # App security
    SECRET_KEY: str = "change-me-in-production-random-secret"

    # Environment
    ENVIRONMENT: str = "development"

    # Mock mode — all external APIs (Gemini, GitHub, Jira, Slack) return fake data
    MOCK_MODE: bool = False
    # Fast demo mode — skips GitHub API calls and uses a pre-cached profile (saves ~10s)
    DEMO_FAST_MODE: bool = False

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
