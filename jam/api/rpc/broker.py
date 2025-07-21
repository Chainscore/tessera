from collections import defaultdict
import asyncio
from typing import Any, AsyncGenerator, Dict, Set

class Broker:
    def __init__(self):
        self.topics: Dict[str, Set[asyncio.Queue]] = defaultdict(set)

    async def publish(self, topic: str, message: Any) -> None:
        for q in set(self.topics[topic]):
            await q.put(message)

    async def subscribe(self, topic: str) -> AsyncGenerator[Any, None]:
        q: asyncio.Queue = asyncio.Queue()
        self.topics[topic].add(q)
        try:
            while True:
                yield await q.get()
        finally:
            self.topics[topic].remove(q)
    
   

broker = Broker()
