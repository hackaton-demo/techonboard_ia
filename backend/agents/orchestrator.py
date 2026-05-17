"""
LangGraph orchestrator — runs the full onboarding pipeline as a stateful graph.

Nodes:
1. analyze_profile   — fetch GitHub profile
2. provision_access  — provision GitHub / Jira / Slack access
3. navigate_codebase — index repo and generate codebase tour
4. assign_ticket     — find and assign the first Jira ticket
5. generate_plan     — generate the 14-day onboarding plan with Gemini Pro
"""

import json
import logging
import uuid
from typing import Any, TypedDict

import google.generativeai as genai
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import get_settings
from agents.profile_analyzer import ProfileAnalyzer
from agents.access_provisioner import AccessProvisioner
from agents.codebase_navigator import CodebaseNavigator
from agents.ticket_assigner import TicketAssigner
from integrations.jira_client import JiraClient

logger = logging.getLogger(__name__)
settings = get_settings()


# ── State definition ──────────────────────────────────────────────────────────

class OnboardingState(TypedDict):
    session_id: str
    agent_profile: dict[str, Any]
    seniority: str
    dev_github_username: str
    dev_email: str
    project_repo_url: str
    interview_profile: dict[str, Any]

    # Outputs populated by each node
    github_profile: dict[str, Any]
    access_status: dict[str, Any]
    codebase_tour: str
    assigned_ticket: dict[str, Any] | None
    onboarding_plan: dict[str, Any]

    # Error tracking
    errors: list[str]


# ── Node implementations ──────────────────────────────────────────────────────

async def analyze_profile(state: OnboardingState) -> OnboardingState:
    """Node 1: Fetch and analyze the developer's GitHub profile."""
    logger.info(f"[Orchestrator] analyze_profile for {state['dev_github_username']}")
    try:
        analyzer = ProfileAnalyzer()
        profile = await analyzer.analyze_github_profile(state["dev_github_username"])
        return {**state, "github_profile": profile}
    except Exception as exc:
        logger.error(f"analyze_profile failed: {exc}")
        errors = state.get("errors", [])
        return {**state, "github_profile": {}, "errors": errors + [f"profile_analysis: {exc}"]}


async def provision_access(state: OnboardingState, db: AsyncSession) -> OnboardingState:
    """Node 2: Provision all accesses via Lobster Trap policy enforcement."""
    logger.info(f"[Orchestrator] provision_access for session {state['session_id']}")
    try:
        from models.onboarding import OnboardingSession

        result = await db.execute(
            select(OnboardingSession).where(
                OnboardingSession.id == state["session_id"]
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {state['session_id']} not found")

        provisioner = AccessProvisioner()
        access_status = await provisioner.provision_all(session, state["agent_profile"])

        # Persist to DB
        session.access_status = access_status
        await db.commit()

        return {**state, "access_status": access_status}
    except Exception as exc:
        logger.error(f"provision_access failed: {exc}")
        errors = state.get("errors", [])
        return {**state, "access_status": {}, "errors": errors + [f"access_provision: {exc}"]}


async def navigate_codebase(state: OnboardingState, db: AsyncSession) -> OnboardingState:
    """Node 3: Index the project repo and generate a personalized codebase tour."""
    logger.info(f"[Orchestrator] navigate_codebase for {state['project_repo_url']}")
    try:
        navigator = CodebaseNavigator(db)

        # Only clone+index if repo URL is valid
        if state["project_repo_url"] and state["project_repo_url"].startswith("http"):
            await navigator.index_repository(
                state["project_repo_url"], state["session_id"]
            )

        learning_sequence = state["agent_profile"].get("learning_sequence", [])
        tour = await navigator.generate_tour(
            learning_sequence=learning_sequence,
            session_context={
                "session_id": state["session_id"],
                "seniority": state["seniority"],
                "interview_profile": state["interview_profile"],
            },
        )
        return {**state, "codebase_tour": tour}
    except Exception as exc:
        logger.error(f"navigate_codebase failed: {exc}")
        errors = state.get("errors", [])
        tour = f"# Codebase Tour\n\nTour generated in demo mode (error: {exc})"
        return {**state, "codebase_tour": tour, "errors": errors + [f"codebase_nav: {exc}"]}


async def assign_ticket(state: OnboardingState) -> OnboardingState:
    """Node 4: Select and assign the ideal first Jira ticket."""
    logger.info(f"[Orchestrator] assign_ticket for {state['dev_github_username']}")
    try:
        jira = JiraClient()
        assigner = TicketAssigner()

        # Get backlog tickets (use a default project key)
        project_key = "DEMO"
        tickets = await jira.get_backlog_tickets(project_key, limit=30)

        ticket_criteria = state["agent_profile"].get("ticket_criteria", {})
        best_ticket = await assigner.find_best_ticket(
            jira_tickets=tickets,
            seniority=state["seniority"],
            interview_profile=state["interview_profile"],
            ticket_criteria=ticket_criteria,
        )

        if best_ticket:
            await assigner.assign_ticket(
                best_ticket["id"], state["dev_github_username"]
            )

        return {**state, "assigned_ticket": best_ticket}
    except Exception as exc:
        logger.error(f"assign_ticket failed: {exc}")
        errors = state.get("errors", [])
        return {**state, "assigned_ticket": None, "errors": errors + [f"ticket_assign: {exc}"]}


async def generate_plan(state: OnboardingState, db: AsyncSession) -> OnboardingState:
    """Node 5: Generate the 14-day onboarding plan with Gemini Pro."""
    logger.info(f"[Orchestrator] generate_plan for session {state['session_id']}")
    try:
        plan = await _build_14_day_plan(state)

        # Persist plan and ticket to DB
        from models.onboarding import OnboardingSession

        result = await db.execute(
            select(OnboardingSession).where(
                OnboardingSession.id == state["session_id"]
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.onboarding_plan = plan
            if state.get("assigned_ticket"):
                session.assigned_ticket_id = state["assigned_ticket"].get("id")
            session.status = "active"
            await db.commit()

        return {**state, "onboarding_plan": plan}
    except Exception as exc:
        logger.error(f"generate_plan failed: {exc}")
        errors = state.get("errors", [])
        return {**state, "onboarding_plan": {}, "errors": errors + [f"plan_generation: {exc}"]}


# ── Plan generation helper ────────────────────────────────────────────────────

async def _build_14_day_plan(state: OnboardingState) -> dict[str, Any]:
    """Use Gemini Pro to generate a structured 14-day onboarding plan."""
    if not settings.GOOGLE_API_KEY:
        return _mock_plan(state)

    try:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        agent_name = state["agent_profile"].get("name", "Developer")
        seniority = state["seniority"]
        interview = state["interview_profile"]
        ticket = state.get("assigned_ticket") or {}

        prompt = f"""
Generate a 14-day onboarding plan for a {seniority} {agent_name}.

PROFILE:
- Current stack: {interview.get("stack_actual", [])}
- Gaps: {interview.get("stack_gaps", [])}
- Learning style: {interview.get("estilo_aprendizaje", "mixed")}
- First ticket: {ticket.get("summary", "Not assigned")} ({ticket.get("id", "N/A")})

TEAM LEARNING SEQUENCE:
{chr(10).join(f"- {s}" for s in state["agent_profile"].get("learning_sequence", []))}

Generate a structured plan in JSON with:
{{
  "title": "Onboarding Plan - {agent_name} {seniority}",
  "duration_days": 14,
  "weeks": [
    {{
      "week": 1,
      "theme": "Week theme",
      "days": [
        {{
          "day": 1,
          "title": "Day title",
          "objectives": ["objective 1", "objective 2"],
          "activities": ["activity 1", "activity 2"],
          "deliverable": "what should be ready at the end of the day"
        }}
      ]
    }}
  ],
  "success_metrics": ["metric 1", "metric 2"],
  "key_contacts": ["person_role_1", "person_role_2"],
  "resources": ["resource 1", "resource 2"]
}}
"""
        response = await model.generate_content_async(prompt)
        text = response.text.strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return json.loads(text)
    except Exception as exc:
        logger.error(f"Gemini plan generation failed: {exc}")
        return _mock_plan(state)


def _mock_plan(state: OnboardingState) -> dict[str, Any]:
    """Return a demo plan when Gemini is not available."""
    return {
        "title": f"Onboarding Plan — {state['agent_profile'].get('name', 'Developer')}",
        "duration_days": 14,
        "weeks": [
            {
                "week": 1,
                "theme": "Setup & Exploration",
                "days": [
                    {"day": i, "title": f"Day {i}", "objectives": ["Environment setup"], "activities": ["Read documentation"], "deliverable": "Working environment"}
                    for i in range(1, 8)
                ],
            },
            {
                "week": 2,
                "theme": "First Ticket & Contribution",
                "days": [
                    {"day": i, "title": f"Day {i}", "objectives": ["Complete first ticket"], "activities": ["Pair programming", "Code review"], "deliverable": "Open PR"}
                    for i in range(8, 15)
                ],
            },
        ],
        "success_metrics": ["First PR merged", "Setup complete", "Ticket completed"],
        "key_contacts": ["Tech Lead", "Assigned buddy"],
        "resources": ["Team wiki", "Project README"],
    }


# ── Graph builder ─────────────────────────────────────────────────────────────

def _build_graph(db: AsyncSession) -> StateGraph:
    """Build the LangGraph onboarding pipeline."""
    graph = StateGraph(OnboardingState)

    async def _provision_access(s: OnboardingState) -> OnboardingState:
        return await provision_access(s, db)

    async def _navigate_codebase(s: OnboardingState) -> OnboardingState:
        return await navigate_codebase(s, db)

    async def _generate_plan(s: OnboardingState) -> OnboardingState:
        return await generate_plan(s, db)

    graph.add_node("analyze_profile", analyze_profile)
    graph.add_node("provision_access", _provision_access)
    graph.add_node("navigate_codebase", _navigate_codebase)
    graph.add_node("assign_ticket", assign_ticket)
    graph.add_node("generate_plan", _generate_plan)

    graph.set_entry_point("analyze_profile")
    graph.add_edge("analyze_profile", "provision_access")
    graph.add_edge("provision_access", "navigate_codebase")
    graph.add_edge("navigate_codebase", "assign_ticket")
    graph.add_edge("assign_ticket", "generate_plan")
    graph.add_edge("generate_plan", END)

    return graph.compile()


async def run_onboarding_pipeline(session_id: str, db: AsyncSession) -> dict[str, Any]:
    """Run the complete onboarding pipeline for a session."""
    from models.onboarding import OnboardingSession
    from models.agent_profile import AgentProfile

    try:
        # Load session from DB
        result = await db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Load agent profile
        agent_result = await db.execute(
            select(AgentProfile).where(AgentProfile.id == session.agent_profile_id)
        )
        agent_profile_row = agent_result.scalar_one_or_none()

        agent_profile_dict: dict[str, Any] = {}
        if agent_profile_row:
            agent_profile_dict = {
                "id": str(agent_profile_row.id),
                "name": agent_profile_row.name,
                "category": agent_profile_row.category,
                "seniority_levels": agent_profile_row.seniority_levels,
                "tools": agent_profile_row.tools,
                "access_rules": agent_profile_row.access_rules,
                "learning_sequence": agent_profile_row.learning_sequence,
                "ticket_criteria": agent_profile_row.ticket_criteria,
                "interview_questions": agent_profile_row.interview_questions,
                "lobster_trap_policy_file": agent_profile_row.lobster_trap_policy_file,
            }

        # Update session status
        session.status = "provisioning"
        await db.commit()

        # Build initial state
        initial_state: OnboardingState = {
            "session_id": session_id,
            "agent_profile": agent_profile_dict,
            "seniority": session.seniority,
            "dev_github_username": session.dev_github_username,
            "dev_email": session.dev_email,
            "project_repo_url": session.project_repo_url,
            "interview_profile": session.interview_profile or {},
            "github_profile": {},
            "access_status": {},
            "codebase_tour": "",
            "assigned_ticket": None,
            "onboarding_plan": {},
            "errors": [],
        }

        graph = _build_graph(db)
        final_state = await graph.ainvoke(initial_state)

        logger.info(
            f"Onboarding pipeline complete for session {session_id}. "
            f"Errors: {final_state.get('errors', [])}"
        )
        return final_state

    except Exception as exc:
        logger.error(f"Onboarding pipeline failed for session {session_id}: {exc}")
        raise
