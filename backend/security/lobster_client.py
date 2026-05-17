"""
Lobster Trap client — Python wrapper around the Veea Lobster Trap proxy.

In development mode, if Lobster Trap is unreachable, the client returns a
mock response so the app continues working without the sidecar.
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class LobsterEvent:
    event_type: str          # REDACT | DENY | LOG | HUMAN_REVIEW
    severity: str            # LOW | MEDIUM | HIGH | CRITICAL
    rule_triggered: str
    action_taken: str
    original_intent: str | None = None
    resource_requested: str | None = None
    redacted_content: str | None = None
    allowed: bool = True
    raw_response: dict = field(default_factory=dict)


class LobsterTrapClient:
    """Async HTTP client for the Lobster Trap DPI proxy."""

    def __init__(self) -> None:
        self._base_url = settings.LOBSTER_TRAP_URL.rstrip("/")
        self._timeout = 10.0

    # ── Public API ────────────────────────────────────────────────────────────

    async def proxy_request(
        self,
        prompt: str,
        session_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a prompt through Lobster Trap and get the (possibly modified) prompt back."""
        payload = {
            "prompt": prompt,
            "session": session_context or {},
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/proxy",
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            return self._dev_fallback("proxy_request", exc, prompt)

    async def check_policy(
        self,
        content: str,
        session: dict[str, Any] | None = None,
    ) -> LobsterEvent:
        """Check whether content passes the policy for the given session."""
        payload = {
            "content": content,
            "session": session or {},
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/policy/check",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return LobsterEvent(
                    event_type=data.get("event_type", "LOG"),
                    severity=data.get("severity", "LOW"),
                    rule_triggered=data.get("rule_triggered", "default"),
                    action_taken=data.get("action_taken", "logged"),
                    original_intent=data.get("original_intent"),
                    resource_requested=data.get("resource_requested"),
                    allowed=data.get("allowed", True),
                    raw_response=data,
                )
        except Exception as exc:
            return self._dev_fallback_event("check_policy", exc)

    async def redact_pii(self, content: str) -> str:
        """Return a PII-redacted version of the content."""
        payload = {"content": content}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/redact",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("redacted_content", content)
        except Exception as exc:
            if settings.is_development:
                logger.debug(f"Lobster Trap redact unavailable ({exc}), returning original")
                return content
            raise

    async def log_event(
        self,
        event: dict[str, Any],
        session_id: str | None = None,
    ) -> None:
        """Fire-and-forget log to Lobster Trap."""
        payload = {"event": event, "session_id": session_id}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                await client.post(f"{self._base_url}/log", json=payload)
        except Exception as exc:
            logger.debug(f"Lobster Trap log unavailable ({exc})")

    # ── Convenience: check access resource ────────────────────────────────────

    async def check_access(
        self,
        resource: str,
        seniority: str,
        agent_category: str,
        session_id: str | None = None,
    ) -> LobsterEvent:
        """Check whether an access provisioning action is allowed."""
        return await self.check_policy(
            content=f"access_request:{resource}",
            session={
                "resource_type": resource,
                "session_seniority": seniority,
                "agent_category": agent_category,
                "session_id": session_id,
                "event_type": "access_request",
            },
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _dev_fallback(
        self, operation: str, exc: Exception, original_content: str = ""
    ) -> dict[str, Any]:
        if settings.is_development:
            logger.debug(f"Lobster Trap '{operation}' unavailable ({exc}) — mock response")
            return {
                "event_type": "LOG",
                "severity": "LOW",
                "rule_triggered": "dev_fallback",
                "action_taken": "logged (development mode)",
                "allowed": True,
                "content": original_content,
                "mock": True,
            }
        logger.error(f"Lobster Trap '{operation}' failed in production: {exc}")
        raise exc

    def _dev_fallback_event(
        self, operation: str, exc: Exception
    ) -> LobsterEvent:
        if settings.is_development:
            logger.debug(f"Lobster Trap '{operation}' unavailable ({exc}) — mock event")
            return LobsterEvent(
                event_type="LOG",
                severity="LOW",
                rule_triggered="dev_fallback",
                action_taken="logged (development mode)",
                allowed=True,
            )
        logger.error(f"Lobster Trap '{operation}' failed in production: {exc}")
        raise exc
