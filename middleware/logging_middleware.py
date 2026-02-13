import time
from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from adrie.core.logger import get_logger
from adrie.middleware.request_id import get_request_id

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging incoming requests and outgoing responses."""
    def __init__(self, app: ASGIApp):
        """Initialize the LoggingMiddleware."""
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the incoming request and log the outgoing response."""
        request_id = get_request_id()  # Get the request ID from the ContextVar

        client_ip = request.client.host if request.client else "N/A"

        # Log incoming request
        logger.info(
            f"Incoming Request: {request.method} {request.url} from {client_ip}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "client_ip": client_ip,
            },
        )

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log outgoing response
        logger.info(
            f"Outgoing Response: {request.method} {request.url} - "
            f"Status {response.status_code} - Took {process_time:.4f}s",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "process_time": process_time,
                "client_ip": client_ip,
            },
        )

        return response
