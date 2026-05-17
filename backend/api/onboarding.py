import uuid
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import get_db
from models.onboarding import OnboardingSession
from models.agent_profile import AgentProfile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class OnboardingCreateRequest(BaseModel):
    agent_id: str
    seniority: str
    dev_email: str
    tx_hash: str | None = None
    dev_github_username: str | None = None
    project_repo_url: str | None = None
    manager_id: str | None = None


class OnboardingStatusResponse(BaseModel):
    id: str
    agent_id: str | None
    agent_name: str | None = None
    agent_emoji: str | None = None
    seniority: str
    dev_email: str
    status: str
    payment_tx_hash: str | None = None
    access_status: dict[str, Any]
    interview_profile: dict[str, Any] | None
    assigned_ticket_id: str | None
    created_at: str

    model_config = {"from_attributes": True}


class OnboardingPlanResponse(BaseModel):
    session_id: str
    status: str
    onboarding_plan: dict[str, Any] | None


async def _resolve_agent(db: AsyncSession, agent_id: str) -> AgentProfile | None:
    query = select(AgentProfile)
    try:
        uid = uuid.UUID(agent_id)
        query = query.where(AgentProfile.id == uid)
    except ValueError:
        query = query.where(AgentProfile.slug == agent_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


def _session_to_response(session: OnboardingSession, agent: AgentProfile | None = None) -> OnboardingStatusResponse:
    return OnboardingStatusResponse(
        id=str(session.id),
        agent_id=str(session.agent_profile_id) if session.agent_profile_id else None,
        agent_name=agent.name if agent else None,
        agent_emoji=agent.icon if agent else None,
        seniority=session.seniority,
        dev_email=session.dev_email or "",
        status=session.status,
        payment_tx_hash=session.payment_tx_hash,
        access_status=session.access_status or {},
        interview_profile=session.interview_profile,
        assigned_ticket_id=session.assigned_ticket_id,
        created_at=session.created_at.isoformat(),
    )


@router.post("", response_model=OnboardingStatusResponse, status_code=status.HTTP_201_CREATED)
async def create_onboarding(
    body: OnboardingCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> OnboardingStatusResponse:
    """Create a new onboarding session (after payment verification)."""
    agent = await _resolve_agent(db, body.agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{body.agent_id}' not found",
        )

    session = OnboardingSession(
        id=uuid.uuid4(),
        agent_profile_id=agent.id,
        seniority=body.seniority,
        dev_email=body.dev_email,
        dev_github_username=body.dev_github_username or "",
        project_repo_url=body.project_repo_url or "",
        status="interviewing",
        payment_tx_hash=body.tx_hash,
        access_status={},
        manager_id=uuid.UUID(body.manager_id) if body.manager_id else None,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    logger.info(f"Created onboarding session {session.id} for {body.dev_email}")
    return _session_to_response(session, agent)


@router.get("/{session_id}", response_model=OnboardingStatusResponse)
async def get_onboarding(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> OnboardingStatusResponse:
    """Get the current status and progress of an onboarding session."""
    try:
        uid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid session ID")

    result = await db.execute(
        select(OnboardingSession).where(OnboardingSession.id == uid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    agent = None
    if session.agent_profile_id:
        result2 = await db.execute(
            select(AgentProfile).where(AgentProfile.id == session.agent_profile_id)
        )
        agent = result2.scalar_one_or_none()

    return _session_to_response(session, agent)


@router.patch("/{session_id}/cancel", response_model=OnboardingStatusResponse)
async def cancel_onboarding(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> OnboardingStatusResponse:
    """Cancel an in-progress onboarding session (keeps history)."""
    try:
        uid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid session ID")

    result = await db.execute(
        select(OnboardingSession).where(OnboardingSession.id == uid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")

    if session.status in ("completed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session is already '{session.status}' and cannot be cancelled",
        )

    session.status = "cancelled"
    await db.commit()
    await db.refresh(session)

    agent = None
    if session.agent_profile_id:
        from models.agent_profile import AgentProfile as AP
        r = await db.execute(select(AP).where(AP.id == session.agent_profile_id))
        agent = r.scalar_one_or_none()

    logger.info(f"Cancelled onboarding session {session_id}")
    return _session_to_response(session, agent)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_onboarding(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Permanently delete an onboarding session and all its data."""
    try:
        uid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid session ID")

    result = await db.execute(
        select(OnboardingSession).where(OnboardingSession.id == uid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")

    await db.delete(session)
    await db.commit()
    logger.info(f"Deleted onboarding session {session_id}")


@router.get("/{session_id}/plan", response_model=OnboardingPlanResponse)
async def get_onboarding_plan(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> OnboardingPlanResponse:
    """Get the generated 14-day onboarding plan for a session."""
    try:
        uid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid session ID")

    result = await db.execute(
        select(OnboardingSession).where(OnboardingSession.id == uid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    return OnboardingPlanResponse(
        session_id=str(session.id),
        status=session.status,
        onboarding_plan=session.onboarding_plan,
    )
