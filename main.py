from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.dependencies import (
    lifespan_executor_shutdown_handler,
)  # Import the shutdown handler
from api.health import router as health_router
from api.routes import router as api_router
from core.config import settings
from core.logger import get_logger
from infrastructure.mission_registry import MissionRegistry # Import the class
from middleware.logging_middleware import LoggingMiddleware
from middleware.rate_limiting_middleware import (
    RateLimitingMiddleware,
)  # Import RateLimitingMiddleware
from middleware.request_id import RequestIdMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Handle startup and shutdown events for the FastAPI application.

    Initializes core ADRIE components and the ThreadPoolExecutor.
    """
    logger.info(
        f"Starting up ADRIE: {settings.APP_NAME} v{settings.APP_VERSION} "
        f"in {settings.ENVIRONMENT} environment."
    )
    # Initialize ThreadPoolExecutor for CPU-bound tasks
    app.state.executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
    logger.info(f"Initialized ThreadPoolExecutor with {settings.MAX_WORKERS} workers.")

    # Initialize MissionRegistry and attach to app state
    app.state.mission_registry = MissionRegistry()
    logger.info(f"Initialized MissionRegistry with ID: {id(app.state.mission_registry)}")


    yield
    logger.info("Shutting down ADRIE.")
    await lifespan_executor_shutdown_handler(app)  # Use the imported shutdown handler
    if hasattr(app.state, "mission_registry"):
        await app.state.mission_registry.clear() # Clear the mission_registry on shutdown


def create_app() -> FastAPI:
    """Factory function to create and configure a FastAPI application instance."""
    _app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Autonomous Disaster Response Intelligence Engine API",
        lifespan=lifespan,
    )

    _app.include_router(api_router)
    _app.include_router(health_router)

    _app.mount("/ui", StaticFiles(directory="ui"), name="ui")


    _app.add_middleware(RequestIdMiddleware)
    _app.add_middleware(LoggingMiddleware)
    _app.add_middleware(RateLimitingMiddleware)  # Add RateLimitingMiddleware

    return _app

app = create_app() # The global app instance, if still desired for non-test runs
