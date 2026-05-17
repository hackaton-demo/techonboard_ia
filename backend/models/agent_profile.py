import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.database import Base


class AgentProfile(Base):
    __tablename__ = "agent_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    seniority_levels: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    icon: Mapped[str] = mapped_column(String(50), nullable=True)

    stack_keywords: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    tools: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    access_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    learning_sequence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)

    ticket_criteria: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    system_prompt_template: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Interview questions stored in JSONB
    interview_questions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Lobster Trap policy file reference
    lobster_trap_policy_file: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Custom agent flag
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Multi-tenant support
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Slug identifier for default agents (e.g. "qa-engineer")
    slug: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)

    __table_args__ = (
        Index("ix_agent_profiles_category", "category"),
        Index("ix_agent_profiles_is_custom", "is_custom"),
    )

    def __repr__(self) -> str:
        return f"<AgentProfile id={self.id} name={self.name}>"
