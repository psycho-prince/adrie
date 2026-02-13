from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from adrie.api.dependencies import (
    lifespan_executor_shutdown_handler,
)  # Import the shutdown handler
from adrie.api.health import router as health_router
from adrie.api.routes import router as api_router
from adrie.core.config import settings
from adrie.core.logger import get_logger
from adrie.infrastructure.mission_registry import mission_registry
from adrie.middleware.logging_middleware import LoggingMiddleware
from adrie.middleware.rate_limiting_middleware import (
    RateLimitingMiddleware,
)  # Import RateLimitingMiddleware
from adrie.middleware.request_id import RequestIdMiddleware

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

    yield
    logger.info("Shutting down ADRIE.")
    await lifespan_executor_shutdown_handler(app)  # Use the imported shutdown handler
    await mission_registry.clear()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous Disaster Response Intelligence Engine API",
    lifespan=lifespan,
)

app.include_router(api_router)
app.include_router(health_router)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitingMiddleware)  # Add RateLimitingMiddleware
