import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.database import Base


class OnboardingSession(Base):
    __tablename__ = "onboarding_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    agent_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )

    seniority: Mapped[str] = mapped_column(String(50), nullable=False)
    dev_email: Mapped[str] = mapped_column(String(255), nullable=False)
    dev_github_username: Mapped[str] = mapped_column(String(255), nullable=False)
    project_repo_url: Mapped[str] = mapped_column(String(512), nullable=False)

    # Status FSM: payment_pending -> interviewing -> provisioning -> active -> completed
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="payment_pending",
    )

    # x402 payment transaction hash
    payment_tx_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Interview result from Gemini
    interview_profile: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Real-time access provisioning status
    access_status: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Generated 14-day onboarding plan
    onboarding_plan: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # First Jira ticket assigned
    assigned_ticket_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Scheduled check-in timestamps
    checkin_day3_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    checkin_day7_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    checkin_day14_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Relationship to AgentProfile
    agent_profile = relationship("AgentProfile", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<OnboardingSession id={self.id} "
            f"dev={self.dev_github_username} status={self.status}>"
        )
