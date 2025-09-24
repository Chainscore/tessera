from collections import defaultdict
import asyncio
from typing import Any, AsyncGenerator, Dict, Set


class Broker:
    def __init__(self):
        self.topics: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self.last_publish: Dict[str, Any] = {}

    async def publish(self, topic: str, message: Any) -> None:
        try:
            if len(set(self.topics[topic])) == 0:
                self.last_publish.pop(topic, None)
            for q in set(self.topics[topic]):
                await q.put(message)
        except Exception as e:
            print("Error in publish", e)

    async def subscribe(self, topic: str) -> AsyncGenerator[Any, None]:
        q: asyncio.Queue = asyncio.Queue()
        self.topics[topic].add(q)
        try:
            while True:
                yield await q.get()
        finally:
            self.topics[topic].remove(q)


broker = Broker()
