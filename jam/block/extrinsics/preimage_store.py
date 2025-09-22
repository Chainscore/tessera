import asyncio
from typing import List

from tsrkit_types import Uint
from tsrkit_types.bytes import Bytes
from tsrkit_types.struct import structure

from jam.types.protocol.core import ServiceId, BlobLength
from jam.logging import get_logger
from jam.types.protocol.crypto import (
    OpaqueHash, Hash
)

@structure
class Preimage:
    """Preimage structure."""

    requester: ServiceId
    blob: Bytes

logger = get_logger("nodeops")

class PreimageStore:
    _store: dict[OpaqueHash, Preimage] = {}

    def __init__(self) -> None:
        self._store = {}

    @classmethod
    def _validate(cls, preimage: Preimage):
        if preimage:
            return True
        return False

    def store(self, preimage: Preimage):

        pi_hash = OpaqueHash(Hash.blake2b(preimage.blob))

        if pi_hash in self._store:
            logger.debug(
                "Duplicate preimage found",
                preimage=preimage.__class__.__name__,
                val=preimage.to_json(),
            )
        else:
            if not self._validate(preimage):
                logger.info(
                    "Invalid preimage found",
                    preimage=preimage.__class__.__name__,
                    val=preimage.to_json(),
                )
            else:
                self._store[pi_hash] = preimage
                from jam.network.protocols.ce_142 import PreImageAnnouncement, CE142Data, Announcement
                pre_image_len = BlobLength(len(preimage.blob))
                anc = Announcement(serviceId=preimage.requester,
                                   hash=pi_hash,
                                   preimage_len=pre_image_len)
                data_len = Uint[32](len(anc.encode()))
                data = CE142Data(len=data_len, announcement=anc)
                asyncio.create_task(PreImageAnnouncement().transmit(data))


    def remove(self, preimage_list: List[Preimage]):
        """Remove the recently included preimage extrinsic"""
        for k in list(self._store.keys()):
            preimage = self._store[k]
            if preimage in preimage_list:
                try:
                    del self._store[k]
                except ValueError as e:
                    logger.debug(
                        "Extrinsic was not collected",
                        preimage=preimage.__class__.__name__,
                        val=preimage.to_json(),
                    )

    def clear(self):
        self._store = {}
