import asyncio
import concurrent.futures
from typing import Any, Callable

from adrie.core.logger import get_logger

logger = get_logger(__name__)


async def run_in_threadpool(
    func: Callable[..., Any],
    executor: concurrent.futures.ThreadPoolExecutor,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Run a synchronous (potentially CPU-bound) function in a separate thread pool.

    Args:
        func (Callable): The synchronous function to run.
        executor (concurrent.futures.ThreadPoolExecutor): The ThreadPoolExecutor
                                                          instance to use.
        *args (Any): Positional arguments to pass to the function.
        **kwargs (Any): Keyword arguments to pass to the function.

    Returns:
        Any: The result of the function execution.

    Raises:
        RuntimeError: If the executor is not provided or is invalid.

    """
    if not isinstance(executor, concurrent.futures.ThreadPoolExecutor):
        logger.error(
            "Invalid or uninitialized ThreadPoolExecutor provided to run_in_threadpool."
        )
        raise RuntimeError("ThreadPoolExecutor not properly initialized or provided.")

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))
