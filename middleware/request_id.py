import uuid
from contextvars import ContextVar
from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Define a ContextVar to store the request ID
request_id_ctx: ContextVar[str] = ContextVar("request_id_ctx", default="")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware for injecting a unique request ID into the request context."""
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Inject a unique request ID into the request context and process the request."""
        # Generate a unique request ID
        request_id = str(uuid.uuid4())

        # Set the request ID in the ContextVar
        token = request_id_ctx.set(request_id)

        # Add the request ID to the response headers for traceability
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        # Reset the ContextVar
        request_id_ctx.reset(token)

        return response


def get_request_id() -> str:
    """Retrieve the current request ID from the ContextVar."""
    return request_id_ctx.get()
