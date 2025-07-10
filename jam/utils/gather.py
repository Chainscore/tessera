import asyncio
from tsrkit_types import TypedVector
from jam.logging import logger

async def gather_with_exceptions(tasks: TypedVector[asyncio.Task]):
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    results = []

    for res in responses:
        if isinstance(res, Exception):
            logger.error(res)
        else:
            results.append(res)

    return results
