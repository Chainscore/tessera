"""
Subscription Manager

Manages subscription lifecycle, tracking, and cleanup.
"""

import time
import itertools
import structlog
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class SubscriptionRecord:
    """Record of an active subscription."""

    sub_id: int
    method: str
    params: list
    connection_id: str
    created_at: float = field(default_factory=time.time)
    message_count: int = 0
    last_message_at: float | None = None


class SubscriptionManager:
    """Manages subscription lifecycle and tracks active subscriptions."""

    def __init__(self):
        self.logger = structlog.get_logger("rpc")
        self._sub_id_counter = itertools.count(1)
        self._subscriptions: dict[int, SubscriptionRecord] = {}
        self._by_method: dict[str, set[int]] = defaultdict(set)
        self._by_connection: dict[str, set[int]] = defaultdict(set)

    def create_subscription(self, method: str, params: list, connection_id: str) -> int:
        """Create a new subscription and return its ID."""
        sub_id = next(self._sub_id_counter)
        record = SubscriptionRecord(
            sub_id=sub_id, method=method, params=params, connection_id=connection_id
        )

        self._subscriptions[sub_id] = record
        self._by_method[method].add(sub_id)
        self._by_connection[connection_id].add(sub_id)

        self.logger.debug(
            "subscription_created",
            sub_id=sub_id,
            method=method,
            connection_id=connection_id,
            active_count=len(self._subscriptions),
        )
        return sub_id

    def unsubscribe(self, sub_id: int) -> bool:
        """Remove a subscription. Returns True if it existed."""
        record = self._subscriptions.pop(sub_id, None)
        if not record:
            return False

        self._by_method[record.method].discard(sub_id)
        if not self._by_method[record.method]:
            del self._by_method[record.method]

        self._by_connection[record.connection_id].discard(sub_id)
        if not self._by_connection[record.connection_id]:
            del self._by_connection[record.connection_id]

        self.logger.debug(
            "subscription_removed",
            sub_id=sub_id,
            method=record.method,
            active_count=len(self._subscriptions),
        )
        return True

    def cleanup_connection(self, connection_id: str) -> int:
        """Remove all subscriptions for a connection. Returns count removed."""
        sub_ids = list(self._by_connection.get(connection_id, set()))
        removed = sum(1 for sid in sub_ids if self.unsubscribe(sid))

        if removed:
            self.logger.debug(
                "connection_cleaned", connection_id=connection_id, count=removed
            )
        return removed

    def record_message(self, sub_id: int) -> None:
        """Record that a message was delivered to a subscription."""
        record = self._subscriptions.get(sub_id)
        if record:
            record.message_count += 1
            record.last_message_at = time.time()

    def get_stats(self) -> dict:
        """Stats for the monitor dashboard."""
        return {
            "active_subscriptions": len(self._subscriptions),
            "by_method": {method: len(sids) for method, sids in self._by_method.items()},
            "by_connection": len(self._by_connection),
        }
