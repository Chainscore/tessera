from typing import cast, List
from tsrkit_types import U8, Bytes
from tsrkit_types.integers import Uint
from tsrkit_types.struct import structure
from jam.log_setup import network_logger as logger
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.connection import NodeConnection

from jam.types.protocol.crypto import Hash, OpaqueHash

@structure
class CE143Data:
    len: Uint[32]
    pre_image_hash: OpaqueHash

    @property
    def is_valid(self):
        if len(self.pre_image_hash.encode()) == self.len:
            return True
        return False


@structure
class CE143Response:
    len: Uint[32]
    pre_image: Bytes

    @property
    def is_valid(self):
        if len(self.pre_image.encode()) == self.len:
            return True
        return False


class PreimageRequest(NetworkProtocol):
    """
    CE 143 Protocol for requesting Preimage

    Protocol Flow:
        Node -> Node

        --> Hash
        --> FIN
        <-- Preimage
        <-- FIN
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-143-preimage-request
    """

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE143

    async def transmit(self, data: CE143Data, client: NodeConnection) -> List[Bytes]:
        """Request Preimage from Node"""

        msg_a = data.pre_image_hash.encode()
        len_a = data.len.encode()

        logger.info("Requesting Pre-image from ", client=str(client))

        try:
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

            if res is not None:
                return res
            else:
                logger.error("Error fetching preimage from: ", peer=client)
        except Exception as e:
            logger.error(Code.BAD_RESPONSE, error=str(e))

    def req_intercept(self, stream_id: int, server: NodeConnection):
        """Intercept & Fetch requested preimage on Node"""
        buffer = server.stream_buffer[stream_id][1:]

        logger.debug("Received Preimage Request")
        try:
            data = CE143Data.decode(buffer)
            data = cast(CE143Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            logger.debug("Fetching Preimage")
            # fetching preimage from preimage store
            from jam.block.extrinsics.preimages import preimg_store

            msg_a = Bytes(b'').encode()

            if preimg_store._store.get(data.pre_image_hash) is not None:
                preimage = preimg_store._store[data.pre_image_hash].blob
                msg_a = preimage.encode()

            # Return requested preimage to client node
            len_a = Uint[32](len(msg_a)).encode()

            # Send Messages with their lengths
            server.stream_and_keep_open(len_a, stream_id)
            server.stream_and_close(msg_a, stream_id)

            logger.info(
                f"📩 Processed preimage query.",
                pi_hash=data.pre_image_hash.hex()[:16] + "...",
                peer=server,
            )
        except Exception as e:
            # Stop Streaming
            server.stop_stream(stream_id, 1)

            logger.error(Code.BAD_RESPONSE, error=str(e))

    def res_intercept(self, stream_id: int, client: NodeConnection):
        """Intercept Requested Preimage"""
        buffer = client.stream_buffer[stream_id]

        try:
            data = CE143Response.decode(buffer)
            data = cast(CE143Response, data)
            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            pi_hash = OpaqueHash(Hash.blake2b(data.pre_image.encode()))

            logger.debug(
                f"Requested Preimage received.", peer=client, stream_id=stream_id, hash=pi_hash[:8]
            )

            return data.pre_image

        except Exception as e:
            logger.error(Code.BAD_RESPONSE, error=str(e))
            return None
