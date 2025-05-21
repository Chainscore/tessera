from collections import defaultdict
from typing import Any, AsyncGenerator, Dict, Set
import asyncio

class Broker:
    def __init__(self) -> None:
        self.topics: Dict[str, Set[asyncio.Queue]] = defaultdict(set)

    async def publish(self, topic: str, message: Dict[str, Any]) -> None:
        for queue in self.topics[topic]:
            await queue.put(message)

    async def subscribe(self, topic: str) -> AsyncGenerator[str, None]:
        queue = asyncio.Queue()
        self.topics[topic].add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self.topics[topic].remove(queue)

broker = Broker()