import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("onboarding_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Event type: REDACT | DENY | LOG | HUMAN_REVIEW
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Severity: LOW | MEDIUM | HIGH | CRITICAL
    severity: Mapped[str] = mapped_column(String(50), nullable=False)

    # Name of the YAML policy rule that triggered this event
    rule_triggered: Mapped[str] = mapped_column(String(255), nullable=False)

    # Human-readable category of the original intent (e.g. "production_access")
    original_intent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Description of what the system did (e.g. "blocked request", "redacted PII")
    action_taken: Mapped[str] = mapped_column(Text, nullable=False)

    # The resource that was requested (e.g. "aws_prod", "production_db")
    resource_requested: Mapped[str | None] = mapped_column(Text, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<AuditEvent id={self.id} "
            f"type={self.event_type} severity={self.severity}>"
        )
