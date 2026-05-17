import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from models.database import get_db
from models.onboarding import OnboardingSession
from models.audit_log import AuditEvent
from models.agent_profile import AgentProfile

logger = logging.getLogger(__name__)
router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/manager")
async def manager_dashboard(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return dashboard data with stats, sessions, and recent audit events."""
    result = await db.execute(
        select(OnboardingSession).order_by(desc(OnboardingSession.created_at))
    )
    sessions = result.scalars().all()

    # Collect unique agent IDs
    agent_ids = {s.agent_profile_id for s in sessions if s.agent_profile_id}
    agents_by_id: dict = {}
    if agent_ids:
        agents_result = await db.execute(
            select(AgentProfile).where(AgentProfile.id.in_(agent_ids))
        )
        for a in agents_result.scalars().all():
            agents_by_id[a.id] = a

    # Compute stats
    status_counts: dict[str, int] = {}
    for s in sessions:
        status_counts[s.status] = status_counts.get(s.status, 0) + 1

    stats = {
        "total": len(sessions),
        "active": status_counts.get("active", 0),
        "completed": status_counts.get("completed", 0),
        "payment_pending": status_counts.get("payment_pending", 0),
        "interviewing": status_counts.get("interviewing", 0),
        "provisioning": status_counts.get("provisioning", 0),
    }

    # Build session list with agent info
    recent_sessions = []
    for s in sessions[:20]:
        agent = agents_by_id.get(s.agent_profile_id) if s.agent_profile_id else None
        recent_sessions.append({
            "id": str(s.id),
            "dev_email": s.dev_email or s.dev_github_username or "",
            "agent_id": str(s.agent_profile_id) if s.agent_profile_id else None,
            "agent_name": agent.name if agent else None,
            "agent_emoji": agent.icon if agent else "🤖",
            "seniority": s.seniority,
            "status": s.status,
            "payment_tx_hash": s.payment_tx_hash,
            "plan_generated": s.onboarding_plan is not None,
            "ticket_assigned": s.assigned_ticket_id,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.created_at.isoformat(),
        })

    # Recent audit events
    audit_result = await db.execute(
        select(AuditEvent).order_by(desc(AuditEvent.timestamp)).limit(10)
    )
    recent_audits = audit_result.scalars().all()

    audit_events = [
        {
            "id": str(e.id),
            "timestamp": e.timestamp.isoformat(),
            "event_type": e.event_type,
            "severity": e.severity,
            "rule_triggered": e.rule_triggered,
            "action_taken": e.action_taken,
            "session_id": str(e.session_id) if e.session_id else None,
            "agent_id": None,
            "details": None,
        }
        for e in recent_audits
    ]

    return {
        "stats": stats,
        "recent_sessions": recent_sessions,
        "audit_events": audit_events,
    }


@router.get("/audit-log")
async def get_audit_log(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    severity: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List Lobster Trap audit events with pagination and filtering."""
    query = select(AuditEvent).order_by(desc(AuditEvent.timestamp))

    if severity:
        query = query.where(AuditEvent.severity == severity.upper())
    if event_type:
        query = query.where(AuditEvent.event_type == event_type.upper())
    if session_id:
        try:
            import uuid
            query = query.where(AuditEvent.session_id == uuid.UUID(session_id))
        except ValueError:
            pass

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * size
    result = await db.execute(query.offset(offset).limit(size))
    events = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
        "items": [
            {
                "id": str(e.id),
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "severity": e.severity,
                "rule_triggered": e.rule_triggered,
                "action_taken": e.action_taken,
                "session_id": str(e.session_id) if e.session_id else None,
                "agent_id": None,
                "details": None,
            }
            for e in events
        ],
    }
