import time
from collections import defaultdict
from typing import Dict, Tuple


class RateLimiter:
    """A simple in-memory rate limiter using the Leaky Bucket algorithm.

    This implementation is for demonstration and single-instance applications.
    For production, consider distributed rate limiters (e.g., Redis-backed).
    """

    def __init__(self, rate_limit: int, interval: int):
        """Initialize the RateLimiter.

        Args:
            rate_limit (int): The maximum number of requests allowed
                              within the interval.
            interval (int): The time window in seconds.

        """
        self.rate_limit = rate_limit
        self.interval = interval
        self.buckets: Dict[str, Tuple[float, int]] = defaultdict(
            lambda: (0.0, 0)
        )  # {key: (last_fill_time, tokens)}

    def allow_request(self, key: str) -> bool:
        """Check if a request from the given key is allowed.

        Args:
            key (str): A unique identifier for the client (e.g., IP address, user ID).

        Returns:
            bool: True if the request is allowed, False otherwise.

        """
        now = time.monotonic()
        last_fill_time, tokens = self.buckets[key]

        # Calculate new tokens based on time elapsed
        elapsed_time = now - last_fill_time
        new_tokens = min(
            self.rate_limit,
            tokens + int(elapsed_time * (self.rate_limit / self.interval)),
        )

        # Update last fill time
        self.buckets[key] = (now, new_tokens)

        if new_tokens >= 1:
            # Consume a token
            self.buckets[key] = (now, new_tokens - 1)
            return True
        else:
            return False


# Example global instance (if needed for direct use, though middleware is preferred)
# from adrie.core.config import settings
# global_rate_limiter = RateLimiter(
#     rate_limit=settings.RATE_LIMIT_REQUESTS_PER_INTERVAL,
#     interval=settings.RATE_LIMIT_INTERVAL_SECONDS
# )
