import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

_DEFAULT_AGENTS_PATH = Path(__file__).parent / "default_agents.json"


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class AgentProfileCreate(BaseModel):
    name: str
    category: str
    seniority_levels: list[str]
    icon: str | None = None
    stack_keywords: list[str] = Field(default_factory=list)
    tools: dict[str, Any] = Field(default_factory=dict)
    access_rules: dict[str, Any] = Field(default_factory=dict)
    learning_sequence: list[str] = Field(default_factory=list)
    ticket_criteria: dict[str, str] = Field(default_factory=dict)
    interview_questions: dict[str, str] = Field(default_factory=dict)
    lobster_trap_policy_file: str | None = None
    system_prompt_template: str | None = None
    is_custom: bool = False
    organization_id: uuid.UUID | None = None
    slug: str | None = None


class AgentProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    seniority_levels: list[str]
    icon: str | None
    stack_keywords: list[str]
    tools: dict[str, Any]
    access_rules: dict[str, Any]
    learning_sequence: list[str]
    ticket_criteria: dict[str, str]
    interview_questions: dict[str, str]
    lobster_trap_policy_file: str | None
    system_prompt_template: str | None
    is_custom: bool
    organization_id: uuid.UUID | None
    created_at: datetime
    slug: str | None

    model_config = {"from_attributes": True}


# ── Loader ────────────────────────────────────────────────────────────────────

def load_default_agents() -> list[dict]:
    """Read default_agents.json and return the list of agent dicts."""
    try:
        with open(_DEFAULT_AGENTS_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("agents", [])
    except FileNotFoundError:
        logger.error(f"default_agents.json not found at {_DEFAULT_AGENTS_PATH}")
        return []
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse default_agents.json: {exc}")
        return []


# ── DB seeder ─────────────────────────────────────────────────────────────────

async def seed_agents_to_db(db: AsyncSession) -> int:
    """Insert the 6 default agents into the DB if they don't already exist.

    Returns the number of agents actually inserted.
    """
    from models.agent_profile import AgentProfile  # avoid circular import

    agents_data = load_default_agents()
    inserted = 0

    for agent_dict in agents_data:
        slug = agent_dict.get("id")  # e.g. "qa-engineer"

        # Check if already seeded (idempotent)
        result = await db.execute(
            select(AgentProfile).where(AgentProfile.slug == slug)
        )
        existing = result.scalar_one_or_none()
        if existing:
            logger.debug(f"Agent '{slug}' already in DB — skipping")
            continue

        profile = AgentProfile(
            id=uuid.uuid4(),
            slug=slug,
            name=agent_dict["name"],
            category=agent_dict["category"],
            seniority_levels=agent_dict.get("seniority_levels", []),
            icon=agent_dict.get("icon"),
            stack_keywords=agent_dict.get("stack_keywords", []),
            tools=agent_dict.get("tools", {}),
            access_rules=agent_dict.get("access_rules", {}),
            learning_sequence=agent_dict.get("learning_sequence", []),
            ticket_criteria=agent_dict.get("ticket_criteria", {}),
            interview_questions=agent_dict.get("interview_questions", {}),
            lobster_trap_policy_file=agent_dict.get("lobster_trap_policy_file"),
            system_prompt_template=agent_dict.get("system_prompt_template"),
            is_custom=False,
        )
        db.add(profile)
        inserted += 1

    if inserted:
        await db.commit()
        logger.info(f"Seeded {inserted} default agent(s) to DB")

    return inserted
