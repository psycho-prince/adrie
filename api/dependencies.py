from concurrent.futures import ThreadPoolExecutor

from fastapi import (
    FastAPI,  # Import FastAPI for type hinting
    Request,
)

from adrie.core.logger import get_logger

logger = get_logger(__name__)


async def get_thread_pool_executor(request: Request) -> ThreadPoolExecutor:
    """Provides the ThreadPoolExecutor from the FastAPI app state."""
    return request.app.state.executor


async def lifespan_executor_shutdown_handler(app: FastAPI) -> None:
    """Handle the shutdown of the ThreadPoolExecutor during the FastAPI lifespan."""
    if hasattr(app.state, "executor") and app.state.executor:
        app.state.executor.shutdown(wait=True)
        logger.info("ThreadPoolExecutor shut down.")
