from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from core.config import settings
from core.logger import get_logger
from infrastructure.rate_limiter import RateLimiter

logger = get_logger(__name__)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware for applying rate limiting to incoming requests."""
    def __init__(self, app: ASGIApp):
        """Initialize the RateLimitingMiddleware."""
        super().__init__(app)
        self.rate_limiter = RateLimiter(
            rate_limit=settings.RATE_LIMIT_REQUESTS_PER_INTERVAL,
            interval=settings.RATE_LIMIT_INTERVAL_SECONDS,
        )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the incoming request and apply rate limiting."""
        # Use client host as the key for rate limiting
        client_ip = request.client.host if request.client else "unknown"

        if not self.rate_limiter.allow_request(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Too many requests."},
                headers={"Retry-After": str(self.rate_limiter.interval)},
            )

        response = await call_next(request)
        return response
