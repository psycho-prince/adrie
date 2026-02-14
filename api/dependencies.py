from concurrent.futures import ThreadPoolExecutor

from fastapi import (
    FastAPI,
    Request,
    Depends,
)

from adrie.core.logger import get_logger
from adrie.infrastructure.mission_registry import MissionRegistry # Import MissionRegistry (class)

logger = get_logger(__name__)

# Define get_mission_registry to expose the singleton instance
def get_mission_registry(request: Request) -> MissionRegistry: # Accept Request
    """Provides the MissionRegistry instance from the FastAPI app state."""
    # This function is intended to be used with FastAPI's Depends and can be overridden in tests.
    return request.app.state.mission_registry # Retrieve from app state

async def get_thread_pool_executor(request: Request) -> ThreadPoolExecutor:
    """Provides the ThreadPoolExecutor from the FastAPI app state."""
    return request.app.state.executor


async def lifespan_executor_shutdown_handler(app: FastAPI) -> None:
    """Handle the shutdown of the ThreadPoolExecutor during the FastAPI lifespan."""
    if hasattr(app.state, "executor") and app.state.executor:
        app.state.executor.shutdown(wait=True)
        logger.info("ThreadPoolExecutor shut down.")
