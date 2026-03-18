import asyncio
from typing import List, Coroutine

from jam.log_setup import logger


async def gather_with_exceptions(tasks: List[asyncio.Task | Coroutine], name: str = None):
    """
    Run tasks concurrently and handle exceptions gracefully.
    
    Unlike asyncio.gather with return_exceptions=True, this logs
    exceptions with full stack traces instead of silently collecting them.
    """
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    results = []

    for i, res in enumerate(responses):
        if isinstance(res, Exception):
            logger.error(
                f"Task {i} in gather failed",
                exc_info=(type(res), res, res.__traceback__),
                **({"task": name} if name else {})
            )
            # Optionally append None for failed tasks
            # results.append(None)
        else:
            results.append(res)

    return results