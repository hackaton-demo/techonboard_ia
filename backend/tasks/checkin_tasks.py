"""
Celery tasks for scheduled check-ins at days 3, 7, and 14 of onboarding.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from celery import Celery

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Celery app ────────────────────────────────────────────────────────────────

celery_app = Celery(
    "techonboard",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
)


# ── Tasks ─────────────────────────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def run_checkin_task(self, session_id: str, day: int) -> dict:
    """Celery task: generate and send a check-in message for a session."""
    try:
        result = asyncio.run(_async_checkin(session_id, day))
        logger.info(f"Check-in day {day} completed for session {session_id}")
        return {"session_id": session_id, "day": day, "status": "sent", "message": result}
    except Exception as exc:
        logger.error(f"Check-in task failed for session {session_id} day {day}: {exc}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for checkin day {day} session {session_id}")
            return {"session_id": session_id, "day": day, "status": "failed", "error": str(exc)}


async def _async_checkin(session_id: str, day: int) -> str:
    """Async implementation of the check-in logic."""
    from models.database import AsyncSessionLocal
    from agents.checkin_agent import CheckinAgent

    async with AsyncSessionLocal() as db:
        agent = CheckinAgent(db)
        message = await agent.run_checkin(session_id, day)
        await agent.send_checkin_slack(session_id, day, message)

        # Update the session's check-in timestamp
        from models.onboarding import OnboardingSession
        from sqlalchemy import select
        import uuid

        result = await db.execute(
            select(OnboardingSession).where(
                OnboardingSession.id == uuid.UUID(session_id)
            )
        )
        session = result.scalar_one_or_none()
        if session:
            now = datetime.now(timezone.utc)
            if day == 3:
                session.checkin_day3_at = now
            elif day == 7:
                session.checkin_day7_at = now
            elif day == 14:
                session.checkin_day14_at = now
            await db.commit()

        return message


def schedule_checkin(session_id: str, day: int) -> None:
    """Schedule a check-in task with ETA based on day number.

    Call this right after the onboarding session is activated.
    """
    eta = datetime.now(timezone.utc) + timedelta(days=day)

    result = run_checkin_task.apply_async(
        kwargs={"session_id": session_id, "day": day},
        eta=eta,
    )
    logger.info(
        f"Scheduled check-in day {day} for session {session_id} "
        f"at {eta.isoformat()} (task_id={result.id})"
    )
    return result


def schedule_all_checkins(session_id: str) -> None:
    """Schedule all three check-ins (days 3, 7, 14) for a session."""
    for day in (3, 7, 14):
        schedule_checkin(session_id, day)
    logger.info(f"Scheduled all check-ins for session {session_id}")
