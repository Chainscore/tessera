import asyncio
from typing import List, Coroutine

from jam.log_setup import logger


async def gather_with_exceptions(tasks: List[asyncio.Task | Coroutine]):
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    results = []

    for res in responses:
        if isinstance(res, Exception):
            logger.error(res)
            # results.append(None)
        else:
            results.append(res)

    return results


# async def main():
#     async def success(): return "ok"
#     async def fail(): raise ValueError("fail")
#
#     task1 = asyncio.create_task(success())
#     task2 = asyncio.create_task(fail())
#
#     print("========================")
#
#     results = await gather_with_exceptions([task1, task2])
#     print(results)  # Output: ['ok'], and logs the ValueError
#
# # Run the async main
# if __name__ == "__main__":
#     asyncio.run(main())
