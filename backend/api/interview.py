"""
WebSocket endpoint for the real-time Gemini interview.
Streams tokens to the frontend as they are generated.
After the interview completes, keeps the WebSocket open so the user can
send extra context while the onboarding pipeline runs in the background.
"""

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from models.database import AsyncSessionLocal
from models.onboarding import OnboardingSession
from models.agent_profile import AgentProfile
from agents.profile_analyzer import ProfileAnalyzer
from agents.orchestrator import run_onboarding_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(tags=["interview"])


@router.websocket("/ws/interview/{session_id}")
async def interview_websocket(
    websocket: WebSocket,
    session_id: str,
) -> None:
    """Stream the Gemini interview to the frontend via WebSocket."""
    await websocket.accept()
    logger.info(f"WebSocket connected for interview session {session_id}")

    interview_ok = False

    async with AsyncSessionLocal() as db:
        try:
            # Load session
            try:
                uid = uuid.UUID(session_id)
            except ValueError:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Invalid session ID"})
                )
                await websocket.close()
                return

            result = await db.execute(
                select(OnboardingSession).where(OnboardingSession.id == uid)
            )
            session = result.scalar_one_or_none()

            if not session:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Session not found"})
                )
                await websocket.close()
                return

            # Load agent profile
            agent_result = await db.execute(
                select(AgentProfile).where(AgentProfile.id == session.agent_profile_id)
            )
            agent_profile_row = agent_result.scalar_one_or_none()

            agent_profile_dict = {}
            if agent_profile_row:
                agent_profile_dict = {
                    "name": agent_profile_row.name,
                    "category": agent_profile_row.category,
                    "tools": agent_profile_row.tools,
                    "learning_sequence": agent_profile_row.learning_sequence,
                    "interview_questions": agent_profile_row.interview_questions,
                    "system_prompt_template": agent_profile_row.system_prompt_template,
                }

            await websocket.send_text(
                json.dumps({"type": "status", "message": "interview_started"})
            )

            # Analyze GitHub profile
            analyzer = ProfileAnalyzer()
            github_profile = await analyzer.analyze_github_profile(
                session.dev_github_username
            )

            await websocket.send_text(
                json.dumps({
                    "type": "github_profile",
                    "data": {
                        "username": github_profile.get("username"),
                        "top_languages": github_profile.get("top_languages", []),
                        "public_repos": github_profile.get("public_repos", 0),
                    }
                })
            )

            # Stream the interview
            full_text = ""
            async for token in analyzer.conduct_interview(
                session_id=session_id,
                agent_profile=agent_profile_dict,
                github_profile=github_profile,
            ):
                if "__RESULT__" in token:
                    # Extract and save the interview result
                    result_json_str = token[token.index("__RESULT__") + len("__RESULT__"):]
                    try:
                        interview_result = json.loads(result_json_str)
                    except json.JSONDecodeError:
                        interview_result = analyzer.extract_interview_result(full_text)

                    # Save interview profile to DB
                    session.interview_profile = interview_result
                    session.status = "provisioning"
                    await db.commit()

                    await websocket.send_text(
                        json.dumps({
                            "type": "interview_complete",
                            "result": interview_result,
                        })
                    )
                else:
                    full_text += token
                    await websocket.send_text(
                        json.dumps({"type": "token", "content": token})
                    )

            # Extract result from full text if not already extracted
            if not session.interview_profile:
                interview_result = analyzer.extract_interview_result(full_text)
                session.interview_profile = interview_result
                await db.commit()

            await websocket.send_text(
                json.dumps({"type": "status", "message": "starting_provisioning"})
            )

            interview_ok = True

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session {session_id}")
            return
        except Exception as exc:
            logger.error(f"Interview WebSocket error for session {session_id}: {exc}")
            try:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": str(exc)})
                )
            except Exception:
                pass
            return

    if not interview_ok:
        return

    # Run pipeline in background with its own DB session
    pipeline_task = asyncio.create_task(_run_pipeline_background(session_id))

    # Keep WebSocket open so the user can add context while the plan generates
    while not pipeline_task.done():
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=2.0)
            try:
                data = json.loads(raw)
                if data.get("type") == "message" and data.get("content"):
                    await websocket.send_text(json.dumps({
                        "type": "token",
                        "content": "Got it! I'll take that into account for your plan. ",
                    }))
            except Exception:
                pass
        except asyncio.TimeoutError:
            continue
        except WebSocketDisconnect:
            logger.info(f"Client disconnected during provisioning for {session_id}")
            return
        except Exception:
            break

    # Notify frontend that the plan is ready
    try:
        await websocket.send_text(json.dumps({"type": "plan_ready"}))
    except Exception:
        pass


async def _run_pipeline_background(session_id: str) -> None:
    """Run the full onboarding pipeline after the interview completes."""
    try:
        async with AsyncSessionLocal() as db:
            logger.info(f"Starting onboarding pipeline for session {session_id}")
            await run_onboarding_pipeline(session_id, db)
            logger.info(f"Onboarding pipeline completed for session {session_id}")
    except Exception as exc:
        logger.error(f"Background pipeline failed for session {session_id}: {exc}")
