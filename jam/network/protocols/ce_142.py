from jam.utils.task_utils import create_safe_task
from typing import cast
from tsrkit_types import Uint, U8
from tsrkit_types.struct import structure

from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.connection import PeerConnection
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.types.protocol.core import BlobLength, ServiceId
from jam.types.protocol.crypto import OpaqueHash
from .ce_143 import PreimageRequest, CE143Data

@structure
class Announcement:
    serviceId: ServiceId
    hash: OpaqueHash
    preimage_len: BlobLength

@structure
class CE142Data:
    len: Uint[32]
    announcement: Announcement

    @property
    def is_valid(self):
        if len(self.announcement.encode()) == self.len:
            return True
        return False


class PreImageAnnouncement(NetworkProtocol):
    """
    CE_142 Protocol for announcing new pre-images to peers.

    Protocol Flow:

        Node -> Validator

        --> Service ID ++ Hash ++ Preimage Length
        --> FIN
        <-- FIN
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-142-preimage-announcement
    """

    _prefix = PrefixType.CE142


    async def transmit(self, data: CE142Data):
        """Announce preimage to Peers"""
        node = self.jam.router.node
        if not node:
            self.logger.error("Node not found to transmit")
            return

        msg_a = data.announcement.encode()
        len_a = data.len.encode()

        self.logger.debug("Announcing new preimage to peers", preimage_hash=data.announcement.hash.hex()[:16] + "...")

        announced_count = 0
        responses = []

        for client in node.all_connected:

            # Send Protocol Prefix
            stream_id = client.stream_and_keep_open(message=self._prefix.encode())

            # set prefix and buffer
            client.stream_prefix[stream_id] = U8(self._prefix)
            client.stream_buffer[stream_id] = b""

            # Send Message with their lengths
            client.stream_and_keep_open(message=len_a, stream_id=stream_id)
            res = await client.close_and_wait(
                message=msg_a, stream_id=stream_id
            )

            if res:
                announced_count += 1
                responses.append(res)
                self.logger.debug(
                    "🖹 Preimage announced to peer",
                    stream_id=stream_id,
                    peer=client
                )

        self.logger.info(
            "Preimage announcement completed",
            preimage_hash=data.announcement.hash.hex()[:16] + "...",
            announced_to=announced_count
        )

        return responses

    async def req_intercept(self, stream_id: int, server: PeerConnection):
        """Intercepting & Process preimage hash from peers."""
        self.logger.debug("Received Preimage Announcement")
        buffer = server.stream_buffer[stream_id][1:]
        try:
            data = CE142Data.decode(buffer)
            data = cast(CE142Data, data)
            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            create_safe_task(self._process_preimage(data.announcement, server), name="process_preimage")

            self.logger.info("Preimage announcement 🖹 processed successfully", stream_id=stream_id)
        except Exception as e:
            # Stop Streaming
            server.stop_stream(stream_id, 1)
            self.logger.error(Code.BAD_RESPONSE, error=str(e))


    async def res_intercept(self, stream_id: int, client: PeerConnection) -> tuple[(bool | None), PeerConnection]:
        """Intercept Acknowledgement"""

        buffer = client.stream_buffer[stream_id]
        if buffer == b"":
            self.logger.debug(
                "Preimage acknowledgement received",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )
            return True, client

        return None, client

    async def _process_preimage(self, anc: Announcement, client: PeerConnection):
        from jam.block.extrinsics.preimages import Preimage

        if not self.pool.preimages._store.get(anc.hash):
            CE_143 = PreimageRequest(self.jam)
            hash_len = Uint[32](len(anc.hash.encode()))
            request_data = CE143Data(len=hash_len, pre_image_hash=anc.hash)
            response = await CE_143.transmit(request_data, client)

            if response:
                if len(response) == anc.preimage_len:
                    pre_img = Preimage(requester=ServiceId(anc.serviceId), blob=response)
                    self.pool.preimages.store(pre_img, jam=self.jam)
            else:
                self.logger.error("Received None preimage")
        else:
            self.logger.info("Preimage not needed")