import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Coroutine, TypeVar

R = TypeVar("R")


async def run_in_threadpool(
    func: Callable[..., R], executor: ThreadPoolExecutor, *args: Any, **kwargs: Any
) -> R:
    """Run a synchronous function in a thread pool to avoid blocking the event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))
