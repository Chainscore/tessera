from jam.network.protocols.ce_139_base import SegmentShardRequestBase, ShardWithJustification, JustifiedResponse
from typing import cast

from jam.config.logging import logger
from jam.merklization import BMRFunctions
from jam.network.quic import QuicServerProtocol
from jam.types.base.integers import Int

from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.work.shard import SegmentsShard

from jam.network.protocols.base import NetworkProtocol, PrefixType

from tests.dummy.utils import create_dummy_bytes12, create_dummy_bytes32

class SegmentShardRequestWithJustifications(SegmentShardRequestBase):
    """
        CE 140 Protocol for Requesting Segments Shards from Assurers

        Protocol Flow:
            Guarantor -> Assurers

            --> [Erasure-Root ++ Shard Index ++ len++[Segment Index]]
            --> FIN
            <-- [Segment Shard, Justification]
            <-- FIN
        Source:
            https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-139140-segment-shard-request
    """
    def __init__(self):
        super().__init__(PrefixType.CE140)

    def server_intercept(self, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        request = self.parse_request(buffer)
        logger.info("Handling CE140 shard + justification request")
        response = JustifiedResponse()
        for item in request:
            shards = create_dummy_bytes12()
            segment_shard = SegmentsShard([
                shards,
                create_dummy_bytes12(),
                create_dummy_bytes12(),
                create_dummy_bytes12(),
                create_dummy_bytes12(),
            ])
            bundle_shard_hash = [Bytes(create_dummy_bytes32())]
            merkle = BMRFunctions()
            justify = merkle.trace_fn(values=segment_shard, index=Int(item.shard_Index))
            justify.extend(bundle_shard_hash)
            item_res = ShardWithJustification(shards=shards, justifications=justify)
            response.append(item_res)

        ack = self._prefix.encode() + response.encode()
        server.stream_and_close(stream_id, ack)

    def client_intercept(self, buffer: bytes, stream_id: int) -> JustifiedResponse:
        response, _ = JustifiedResponse.decode_from(buffer)
        response = cast(JustifiedResponse, response)
        logger.info(f"client response: {response}")
        logger.info("Received CE140 shard+justification response")

        return response