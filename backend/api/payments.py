"""
x402 Payment endpoints.

Manual flow (existing frontend):
  POST /payments/activate  → HTTP 402 + payment details (wallet, amount, URL)
  POST /payments/verify    → verify tx_hash (demo_* accepted, 0x... via facilitator)

x402 middleware demo:
  GET  /payments/protected → protected by PaymentMiddlewareASGI (real USDC required)
                             returns agent catalog info after payment
"""

import logging

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from payments.x402_handler import x402PaymentHandler
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/payments", tags=["payments"])

_handler = x402PaymentHandler()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ActivateAgentRequest(BaseModel):
    agent_id: str
    seniority: str
    dev_email: str


class PaymentRequestResponse(BaseModel):
    session_id: str
    amount_usdc: float
    wallet_address: str
    network: str
    payment_url: str
    memo: str | None = None


class VerifyPaymentRequest(BaseModel):
    tx_hash: str


class VerifyPaymentResponse(BaseModel):
    verified: bool


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/activate", status_code=status.HTTP_402_PAYMENT_REQUIRED)
async def activate_agent(
    body: ActivateAgentRequest,
    response: Response,
) -> PaymentRequestResponse:
    """
    Return HTTP 402 with payment details.
    Client completes payment (USDC on Base Sepolia) then calls /verify.
    """
    payment_data = _handler.create_payment_request(
        agent_id=body.agent_id,
        seniority=body.seniority,
    )

    response.headers["X-Payment-Required"] = "true"
    response.headers["X-Payment-Amount"] = str(payment_data.amount)
    response.headers["X-Payment-Currency"] = "USDC"
    response.headers["X-Payment-Wallet"] = payment_data.wallet_address
    response.headers["X-Payment-Network"] = payment_data.network
    response.headers["X-Payment-URL"] = payment_data.payment_url
    response.status_code = status.HTTP_402_PAYMENT_REQUIRED

    logger.info(
        "HTTP 402: agent=%s seniority=%s amount=%.2f USDC network=%s",
        body.agent_id, body.seniority, payment_data.amount, payment_data.network,
    )

    return PaymentRequestResponse(
        session_id=payment_data.session_id,
        amount_usdc=payment_data.amount,
        wallet_address=payment_data.wallet_address,
        network=payment_data.network,
        payment_url=payment_data.payment_url,
        memo=f"TechOnboard-{body.agent_id}-{body.seniority}",
    )


@router.post("/verify", response_model=VerifyPaymentResponse)
async def verify_payment(body: VerifyPaymentRequest) -> VerifyPaymentResponse:
    """
    Verify a payment.
    - demo_*  → accepted instantly (demo mode)
    - 0x...   → verified through x402 facilitator
    """
    verified = await _handler.verify_payment(body.tx_hash)
    return VerifyPaymentResponse(verified=verified)


@router.get("/protected")
async def protected_resource() -> dict:
    """
    This endpoint is guarded by PaymentMiddlewareASGI (x402 SDK).

    Without payment: middleware returns HTTP 402 with PAYMENT-REQUIRED header
    containing the x402 payment requirements (amount, wallet, network).

    With valid X-PAYMENT header: returns onboarding agent pricing info.
    """
    return {
        "message": "Payment verified by x402 middleware",
        "network": settings.X402_NETWORK,
        "facilitator": settings.X402_FACILITATOR_URL,
        "pricing": {
            "junior": settings.X402_PRICE_JUNIOR,
            "mid_senior": settings.X402_PRICE_MID_SENIOR,
            "staff_lead": settings.X402_PRICE_STAFF,
            "currency": "USDC",
        },
        "wallet": settings.X402_WALLET_ADDRESS,
    }


@router.get("/info")
async def payment_info() -> dict:
    """Public endpoint — returns x402 payment configuration (no payment required)."""
    return {
        "protocol": "x402",
        "network": settings.X402_NETWORK,
        "currency": "USDC",
        "facilitator": settings.X402_FACILITATOR_URL,
        "wallet": settings.X402_WALLET_ADDRESS,
        "pricing": {
            "junior": settings.X402_PRICE_JUNIOR,
            "mid_senior": settings.X402_PRICE_MID_SENIOR,
            "staff_lead": settings.X402_PRICE_STAFF,
        },
    }
