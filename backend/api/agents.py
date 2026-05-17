import uuid
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from models.database import get_db
from models.agent_profile import AgentProfile
from catalog.agent_profiles import AgentProfileCreate, AgentProfileResponse
from catalog.prompt_generator import generate_system_prompt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])


class AgentCreateRequest(BaseModel):
    name: str
    category: str
    seniority_levels: list[str]
    icon: str | None = None
    stack_keywords: list[str] = []
    tools: dict[str, Any] = {}
    access_rules: dict[str, Any] = {}
    learning_sequence: list[str] = []
    ticket_criteria: dict[str, str] = {}
    team_stack: str = ""
    company_name: str = "TechOnboard"


class AgentUpdateRequest(BaseModel):
    name: str | None = None
    category: str | None = None
    seniority_levels: list[str] | None = None
    icon: str | None = None
    stack_keywords: list[str] | None = None
    tools: dict[str, Any] | None = None
    access_rules: dict[str, Any] | None = None
    learning_sequence: list[str] | None = None
    ticket_criteria: dict[str, str] | None = None
    system_prompt_template: str | None = None


@router.get("", response_model=list[AgentProfileResponse])
async def list_agents(
    db: AsyncSession = Depends(get_db),
) -> list[AgentProfileResponse]:
    """List all agent profiles (default + custom)."""
    result = await db.execute(
        select(AgentProfile).order_by(AgentProfile.is_custom, AgentProfile.name)
    )
    agents = result.scalars().all()
    return [AgentProfileResponse.model_validate(a) for a in agents]


@router.get("/{agent_id}", response_model=AgentProfileResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> AgentProfileResponse:
    """Get details of a specific agent by ID or slug."""
    # Try by UUID first
    query = select(AgentProfile)
    try:
        uid = uuid.UUID(agent_id)
        query = query.where(AgentProfile.id == uid)
    except ValueError:
        # Try by slug
        query = query.where(AgentProfile.slug == agent_id)

    result = await db.execute(query)
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )
    return AgentProfileResponse.model_validate(agent)


@router.post("", response_model=AgentProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    body: AgentCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentProfileResponse:
    """Create a custom agent. Gemini Pro generates the system_prompt_template."""
    # Generate system prompt via Gemini
    agent_data = body.model_dump()
    system_prompt = await generate_system_prompt(
        agent_data=agent_data,
        team_stack=body.team_stack,
        company_name=body.company_name,
    )

    agent = AgentProfile(
        id=uuid.uuid4(),
        name=body.name,
        category=body.category,
        seniority_levels=body.seniority_levels,
        icon=body.icon,
        stack_keywords=body.stack_keywords,
        tools=body.tools,
        access_rules=body.access_rules,
        learning_sequence=body.learning_sequence,
        ticket_criteria=body.ticket_criteria,
        interview_questions={},
        system_prompt_template=system_prompt,
        is_custom=True,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    logger.info(f"Created custom agent '{agent.name}' (id={agent.id})")
    return AgentProfileResponse.model_validate(agent)


@router.put("/{agent_id}", response_model=AgentProfileResponse)
async def update_agent(
    agent_id: str,
    body: AgentUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentProfileResponse:
    """Update a custom agent profile."""
    try:
        uid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid agent ID")

    result = await db.execute(select(AgentProfile).where(AgentProfile.id == uid))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    if not agent.is_custom:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Default agents cannot be modified",
        )

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    await db.commit()
    await db.refresh(agent)
    return AgentProfileResponse.model_validate(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a custom agent."""
    try:
        uid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid agent ID")

    result = await db.execute(select(AgentProfile).where(AgentProfile.id == uid))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    if not agent.is_custom:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Default agents cannot be deleted",
        )

    await db.delete(agent)
    await db.commit()
