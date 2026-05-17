"""
TechOnboard — FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from models.database import init_db, AsyncSessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Startup / shutdown ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle handler."""
    logger.info("Starting TechOnboard backend...")

    # Init database tables and pgvector extension
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as exc:
        logger.error(f"Database initialization failed: {exc}")

    # Seed default agents
    try:
        async with AsyncSessionLocal() as db:
            from catalog.agent_profiles import seed_agents_to_db
            inserted = await seed_agents_to_db(db)
            if inserted:
                logger.info(f"Seeded {inserted} default agents")
            else:
                logger.info("Default agents already seeded")
    except Exception as exc:
        logger.error(f"Agent seeding failed: {exc}")

    logger.info(f"TechOnboard running in {settings.ENVIRONMENT} mode")
    yield

    logger.info("Shutting down TechOnboard backend")


# ── App factory ────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="TechOnboard API",
        description="AI-powered technical onboarding platform for engineering teams",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    from api.agents import router as agents_router
    from api.onboarding import router as onboarding_router
    from api.interview import router as interview_router
    from api.payments import router as payments_router
    from api.dashboard import router as dashboard_router

    PREFIX = "/api/v1"
    app.include_router(agents_router, prefix=PREFIX)
    app.include_router(onboarding_router, prefix=PREFIX)
    app.include_router(interview_router)  # WebSocket at /ws/interview/{id}, no prefix
    app.include_router(payments_router, prefix=PREFIX)
    app.include_router(dashboard_router, prefix=PREFIX)

    # x402 payment middleware — protects routes defined in build_x402_routes()
    try:
        from x402.http.middleware.fastapi import PaymentMiddlewareASGI
        from payments.x402_handler import build_x402_server, build_x402_routes

        x402_server = build_x402_server()
        x402_routes = build_x402_routes()

        if x402_server and x402_routes:
            app.add_middleware(
                PaymentMiddlewareASGI,
                routes=x402_routes,
                server=x402_server,
            )
            logger.info("x402 PaymentMiddlewareASGI registered on %d route(s)", len(x402_routes))
        else:
            logger.warning("x402 middleware skipped — server or routes not configured")
    except ImportError:
        logger.warning("x402 SDK not installed — skipping PaymentMiddlewareASGI")

    # Health check
    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        return {
            "status": "ok",
            "service": "techonboard-backend",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level="info",
    )
