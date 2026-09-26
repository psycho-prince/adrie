from typing import Any, Dict

from fastapi import APIRouter, status

router = APIRouter()


@router.get(
    "/health",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
)
async def health_check() -> Dict[str, Any]:
    """Return the health status of the application."""
    return {"status": "ok", "message": "Application is healthy."}


@router.get(
    "/ready",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Readiness check endpoint",
)
async def readiness_check() -> Dict[str, Any]:
    """Return the readiness status of the application.

    This can include checks for database connections, external services, etc.
    """
    # Placeholder for more complex readiness checks
    return {"status": "ready", "message": "Application is ready to serve traffic."}
