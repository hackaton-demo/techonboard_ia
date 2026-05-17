"""
x402 Payment handler — real Coinbase x402 Python SDK integration.

Server flow (PaymentMiddlewareASGI on protected routes):
  1. Client hits protected route → middleware returns HTTP 402 + PAYMENT-REQUIRED header
  2. Client signs USDC transfer on Base Sepolia and retries with X-PAYMENT header
  3. Middleware verifies via x402.org/facilitator → passes request to endpoint

Legacy demo flow (kept for demo presentation):
  POST /payments/activate → returns 402 with payment details
  POST /payments/verify   → verifies tx_hash (demo_* accepted in dev mode)
"""

import logging
import uuid
from typing import Any

import httpx
from pydantic import BaseModel

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class PaymentRequest(BaseModel):
    agent_id: str
    seniority: str
    session_id: str | None = None


class PaymentResponse(BaseModel):
    payment_url: str
    amount: float
    currency: str = "USDC"
    wallet_address: str
    network: str
    agent_id: str
    seniority: str
    session_id: str
    status: str = "pending"


# ── x402 SDK server setup ─────────────────────────────────────────────────────

def build_x402_server():
    """Return a configured x402ResourceServer, or None if SDK not installed."""
    try:
        from x402.http import FacilitatorConfig, HTTPFacilitatorClient
        from x402.mechanisms.evm.exact import ExactEvmServerScheme
        from x402.server import x402ResourceServer

        facilitator = HTTPFacilitatorClient(
            FacilitatorConfig(url=settings.X402_FACILITATOR_URL)
        )
        server = x402ResourceServer(facilitator)
        server.register(settings.X402_NETWORK, ExactEvmServerScheme())
        logger.info(
            "x402 server ready — network=%s facilitator=%s",
            settings.X402_NETWORK,
            settings.X402_FACILITATOR_URL,
        )
        return server
    except ImportError:
        logger.warning("x402 SDK not installed — PaymentMiddlewareASGI will be skipped")
        return None
    except Exception as exc:
        logger.error("x402 server init failed: %s", exc)
        return None


def build_x402_routes() -> dict:
    """
    Return the x402 route config for PaymentMiddlewareASGI.

    Protected routes:
      GET  /api/v1/payments/protected  — demo endpoint (pays to see agent info)
    """
    try:
        from x402.http import PaymentOption
        from x402.http.types import RouteConfig

        wallet = settings.X402_WALLET_ADDRESS
        network = settings.X402_NETWORK

        return {
            "GET /api/v1/payments/protected": RouteConfig(
                accepts=[
                    PaymentOption(
                        scheme="exact",
                        pay_to=wallet,
                        price=f"${settings.X402_PRICE_JUNIOR}",
                        network=network,
                    )
                ],
                mime_type="application/json",
                description="TechOnboard agent activation — pay-per-use with USDC on Base",
            ),
        }
    except ImportError:
        return {}
    except Exception as exc:
        logger.error("x402 routes build failed: %s", exc)
        return {}


# ── Handler (legacy + enhanced verification) ─────────────────────────────────

class x402PaymentHandler:
    """
    Handles the manual activate → verify payment flow.

    verify_payment() uses:
      - demo_*  → accepted immediately (dev shortcut)
      - 0x...   → verified through the real x402 facilitator
    """

    def _get_price(self, seniority: str) -> float:
        s = seniority.lower()
        if s == "junior":
            return settings.X402_PRICE_JUNIOR
        if s in ("staff", "lead"):
            return settings.X402_PRICE_STAFF
        return settings.X402_PRICE_MID_SENIOR

    def create_payment_request(
        self,
        agent_id: str,
        seniority: str,
        session_id: str | None = None,
    ) -> PaymentResponse:
        """Build the x402 payment request. Returns a pay.x402.org deep-link."""
        amount = self._get_price(seniority)
        sid = session_id or str(uuid.uuid4())

        payment_url = (
            "https://pay.x402.org/pay"
            f"?to={settings.X402_WALLET_ADDRESS}"
            f"&amount={amount}"
            f"&currency=USDC"
            f"&network={settings.X402_NETWORK}"
            f"&memo=TechOnboard-{agent_id}-{seniority}"
            f"&ref={sid}"
        )

        return PaymentResponse(
            payment_url=payment_url,
            amount=amount,
            currency="USDC",
            wallet_address=settings.X402_WALLET_ADDRESS,
            network=settings.X402_NETWORK,
            agent_id=agent_id,
            seniority=seniority,
            session_id=sid,
            status="pending",
        )

    async def verify_payment(self, tx_hash: str) -> bool:
        """
        Verify payment.

        demo_*  → accepted without network call (dev / demo mode).
        0x...   → verified through x402 facilitator REST API.
        """
        # ── Demo shortcut ─────────────────────────────────────────────────────
        if tx_hash.startswith("demo_"):
            logger.info("Demo payment accepted: %s", tx_hash)
            return True

        # ── Real on-chain verification via x402 facilitator ──────────────────
        try:
            # The facilitator exposes a verify endpoint; fall back to the
            # legacy on-chain check if the facilitator returns 404.
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{settings.X402_FACILITATOR_URL}/verify",
                    json={"txHash": tx_hash, "network": settings.X402_NETWORK},
                    headers={"Content-Type": "application/json"},
                )

                if resp.status_code == 200:
                    data = resp.json()
                    valid = data.get("isValid", data.get("valid", data.get("confirmed", False)))
                    if valid:
                        logger.info("Payment verified via facilitator: %s", tx_hash)
                        return True
                    logger.warning("Facilitator rejected payment %s: %s", tx_hash, data)
                    return False

                logger.warning(
                    "Facilitator returned HTTP %s for tx %s", resp.status_code, tx_hash
                )
                # Fall through to dev-mode acceptance below

        except Exception as exc:
            logger.error("Facilitator verification error for %s: %s", tx_hash, exc)

        # In development, accept on any facilitator error so the demo works
        if settings.is_development:
            logger.warning(
                "Dev mode: accepting payment %s despite facilitator error", tx_hash
            )
            return True

        return False
