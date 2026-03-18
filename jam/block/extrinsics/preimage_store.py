import asyncio
from typing import TYPE_CHECKING, List

import structlog

from tsrkit_types import Uint

from jam.types.protocol.core import BlobLength
from jam.types.protocol.crypto import (
    OpaqueHash, Hash
)

if TYPE_CHECKING:
    from jam.block.extrinsics.preimages import Preimage
    from jam.jam_node import JamNode

class PreimageStore:
    _store: dict[OpaqueHash, "Preimage"] = {}

    def __init__(self) -> None:
        self._store = {}
        self.logger = structlog.get_logger("node")

    def store(self, preimage: "Preimage", jam: "JamNode" = None):

        pi_hash = OpaqueHash(Hash.blake2b(preimage.blob))

        if pi_hash in self._store:
            self.logger.debug(
                "Duplicate preimage found",
                preimage=preimage.__class__.__name__,
                val=preimage.blob[:16],
            )
        else:
            self._store[pi_hash] = preimage
            asyncio.create_task(self.announce(preimage, pi_hash, jam))

    @staticmethod
    async def announce(preimage: "Preimage", pi_hash: OpaqueHash, jam: "JamNode" = None):
        from jam.network.protocols.ce_142 import CE142Data, Announcement
        if not jam or not jam._router:
            return
        pre_image_len = BlobLength(len(preimage.blob))
        anc = Announcement(serviceId=preimage.requester,
                           hash=pi_hash,
                           preimage_len=pre_image_len)
        data_len = Uint[32](len(anc.encode()))
        data = CE142Data(len=data_len, announcement=anc)
        await jam.router.dispatch(142, data)


    def remove(self, preimage_list: List["Preimage"]):
        """Remove the recently included preimage extrinsic"""
        for k in list(self._store.keys()):
            preimage = self._store[k]
            if preimage in preimage_list:
                try:
                    del self._store[k]
                except ValueError as e:
                    self.logger.debug(
                        "Extrinsic was not collected",
                        preimage=preimage.__class__.__name__,
                        val=preimage.blob[:16],
                    )

    def clear(self):
        self._store = {}
