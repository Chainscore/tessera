from jam.network.protocols.ce_139_base import SegmentShardRequestBase, Response
from typing import cast

from jam.config.logging import logger
from jam.network.quic import QuicServerProtocol

from jam.network.protocols.base import NetworkProtocol, PrefixType

from tests.dummy.utils import create_dummy_bytes12, create_dummy_bytes32


class SegmentShardRequest(SegmentShardRequestBase):
    """
        CE 139 Protocol for Requesting Segments Shards from Assurers

        Protocol Flow:
            Guarantor -> Assurers

            --> [Erasure-Root ++ Shard Index ++ len++[Segment Index]]
            --> FIN
            <-- [Segment Shard]
            <-- FIN
        Source:
            https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-139140-segment-shard-request
    """
    def __init__(self):
        super().__init__(PrefixType.CE139)

    def server_intercept(self, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        request = self.parse_request(buffer)
        logger.info("Handling CE139 shard request")

        # Fetch segments...
        response = Response([create_dummy_bytes12()])
        ack = self._prefix.encode() + response.encode()
        server.stream_and_close(stream_id, ack)

    def client_intercept(self, buffer: bytes, stream_id: int):
        response, _ = Response.decode_from(buffer)
        response = cast(Response, response)
        logger.info(f"Received CE139 shard response: {response}")