"""
Message Broker

Pub/sub system for subscription updates.
"""

import asyncio
import time as _time
import structlog
from collections import deque
from typing import Any, AsyncGenerator, Dict, Set


class Broker:
    """
    Pub/sub broker for RPC subscriptions.

    Topic generation happens internally from method + params.
    Uses json_default to automatically serialize params (bytes→b64, Uint→int, etc.)
    """

    def __init__(self):
        self.logger = structlog.get_logger("rpc")
        # topic -> set of queues
        self._topics: Dict[str, Set[asyncio.Queue]] = {}
        # Recent publish history for monitor dashboard
        self._history: deque = deque(maxlen=8)

    @staticmethod
    def make_topic(method: str, params: list) -> str:
        """Generate topic string from method and params."""
        from jam.api.rpc.utils.serialization import json_default

        parts = [method]
        for p in params:
            serialized = json_default(p)
            parts.append(str(serialized))

        topic = ":".join(parts)
        return topic

    async def publish(self, method: str, params: list, message: Any) -> int:
        """
        Publish a message to a topic generated from method + params.

        Args:
            method: Subscription method name (e.g., "subscribeBestBlock")
            params: Parameters for the subscription (raw values, will be serialized)
            message: Message to publish (raw data)

        Returns:
            Number of subscribers that received the message
        """
        topic = self.make_topic(method, params)

        # Get subscribers
        queues = set(self._topics.get(topic, set()))

        if not queues:
            return 0

        # Publish to all subscribers
        delivered = 0
        for queue in queues:
            try:
                await queue.put(message)
                delivered += 1
                self.logger.trace("Publish: delivered", topic=topic, delivered=delivered)
            except Exception as e:
                self.logger.error("Publish: failed!", topic=topic, error=str(e))

        self._history.append((_time.time(), method, delivered))
        return delivered

    async def subscribe(self, method: str, params: list) -> AsyncGenerator[Any, None]:
        """
        Subscribe to a topic generated from method + params.

        Args:
            method: Subscription method name
            params: Parameters for the subscription (raw values from JSON)

        Yields:
            Messages published to the topic
        """
        topic = self.make_topic(method, params)
        queue: asyncio.Queue = asyncio.Queue()
        self._topics.setdefault(topic, set()).add(queue)

        self.logger.trace(
            "Subscribe: topic registered",
            topic=topic,
        )

        try:
            while True:
                message = await queue.get()
                yield message
        finally:
            # Cleanup on unsubscribe
            self._topics[topic].discard(queue)

            # Clean up empty topics
            if not self._topics[topic]:
                del self._topics[topic]

            self.logger.trace(
                "Unsubscribed",
                topic=topic,
                remaining_subscribers=len(self._topics.get(topic, set())),
            )
