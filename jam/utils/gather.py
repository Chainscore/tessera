import asyncio
from typing import List

from jam.logging import logger

async def gather_with_exceptions(tasks: List[asyncio.Task]):
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    results = []

    for res in responses:
        if isinstance(res, Exception):
            logger.error(res)
        else:
            results.append(res)

    return results
