"""
Subscription Publisher

Publishes subscription updates when events occur.
Called by other parts of the system when state changes.
"""

from typing import TYPE_CHECKING

from jam.types import OpaqueHash
from jam.types import WorkPackageHash
from tsrkit_types.bytes import Bytes
from jam.api.rpc.handlers.base import BaseHandler
from jam.types.state.delta import Timestamps

if TYPE_CHECKING:
    from jam.types.state.pi import Pi
    from jam.api.rpc.broker import Broker
    from jam.jam_node import JamNode
    from jam.types.protocol.crypto import HeaderHash
    from jam.types.protocol.core import TimeSlot, ServiceId, BlobLength
    from jam.types.state.delta import AccountMetadata


class SubscriptionPublisher(BaseHandler):
    """
    Publishes subscription updates.

    This class provides methods for publishing subscription updates
    when events occur in the system (new blocks, state changes, etc.)

    Methods are called by other parts of the codebase when relevant
    events happen. They do NOT handle the initial subscription data
    (that's done by calling the regular handlers).

    Note: Broker automatically serializes params using json_default,
    so we pass raw values (bytes, etc.) directly.
    """

    def __init__(self, jam_node: "JamNode", broker: "Broker"):
        super().__init__(jam_node)
        self._broker = broker

    def rpc_check(self) -> bool:
        if not self.settings.rpc_flag:
            return False
        return True

    async def publish_sync_status(self, status: str) -> None:
        """Publish sync status update."""
        if not self.rpc_check():
            return
        await self._broker.publish("subscribeSyncStatus", [], status)

    async def publish_best_block(self, header_hash: "HeaderHash", slot: "TimeSlot") -> None:
        """Publish best block update."""
        if not self.rpc_check():
            return
        await self._broker.publish(
            "subscribeBestBlock",
            [],
            {"header_hash": header_hash, "slot": slot},
        )


    async def publish_finalized_block(self, header_hash: "HeaderHash", slot: "TimeSlot") -> None:
        """Publish finalized block update."""
        if not self.rpc_check():
            return
        await self._broker.publish(
            "subscribeFinalizedBlock",
            [],
            {"header_hash": header_hash, "slot": slot},
        )

    async def _publish_w_finalized(self, method: str, params: list, value):
        if not self.rpc_check():
            return
        # TODO: I don't think it is correct way
        # Ideally it is expected that updates on the required chain must be published
        # There can be forks and not necessary that the changes pushed on best chain handle forks
        # Or even its not guaranteed that the changes pushed are actually via finalized block or not
        # Current version just pushes any updates on both trackers.
        for finality in [True, False]:
            block = self.grandpa.load_final() if finality else self.grandpa.load_best()
            if block:
                await self._broker.publish(
                    method,
                    [*params, finality],
                    {"header_hash": block.header.hash(), "slot": block.header.slot, "value": value},
                )

    async def publish_statistics(self, pi: "Pi") -> None:
        """Publish statistics update."""
        await self._publish_w_finalized(
            "subscribeStatistics",
            [],
            pi
        )

    async def publish_service_data(
        self, service_id: "ServiceId", account_metadata: "AccountMetadata"
    ) -> None:
        """Publish service data update."""
        await self._publish_w_finalized(
            "subscribeServiceData",
            [service_id],
            account_metadata
        )

    async def publish_service_value(
        self, service_id: "ServiceId", key: "Bytes", value: bytes | None
    ) -> None:
        """Publish service value update."""
        await self._publish_w_finalized(
            "subscribeServiceValue",
            [service_id, key],
            value
        )

    async def publish_service_preimage(
        self, service_id: "ServiceId", preimage_hash: "OpaqueHash", preimage: "Bytes"
    ) -> None:
        """Publish service preimage update."""
        await self._publish_w_finalized(
            "subscribeServicePreimage",
            [service_id, preimage_hash],
            preimage
        )

    async def publish_service_request(
        self, service_id: "ServiceId", preimage_hash: "OpaqueHash", preimage_len: "BlobLength", lookup: Timestamps | None
    ) -> None:
        """Publish service request update."""
        await self._publish_w_finalized(
            "subscribeServiceRequest",
            [service_id, preimage_hash, preimage_len],
            lookup
        )

    async def publish_work_package_status(
        self, wp_hash: "WorkPackageHash", anchor_hash: "HeaderHash", status: dict
    ) -> None:
        """Publish work package status update."""
        await self._publish_w_finalized(
            "subscribeWorkPackageStatus",
            [wp_hash, anchor_hash],
            status
        )
