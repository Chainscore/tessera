from jam.config.settings import settings
from jam.network.protocols.ce_139_base import SegmentShardRequestBase, Response
from typing import cast

from jam.config.logging import logger
from jam.network.quic import QuicServerProtocol

from jam.network.protocols.base import PrefixType
from jam.storage.db.kv import KVStore
from jam.types.work.shard import SegmentsShard
from jam.work_package.stores.mappings import ErasureShardsMap
from jam.work_package.stores.segments import SegmentShardsDA
from jam.types.base.integers.fixed import U16
from tests.dummy.utils import create_dummy_bytes12


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
    from jam.network.node import Node

    def __init__(self):
        super().__init__(PrefixType.CE139)

    def server_intercept(self, node: Node, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        request = self.parse_request(buffer)
        logger.info("Handling CE139 shard request")
        d3l = settings.d3l
        er_shards_db = ErasureShardsMap(d3l)
        ss_da = SegmentShardsDA(d3l)

        # Fetching segments...
        response = Response()
        for item in request:
            ss_key = er_shards_db.get_ss_root(root=item.erasure_root, shard_index=item.shard_Index)
            seg_shards: SegmentsShard = ss_da.get(root=ss_key.segment_shard_root)[0]
            for index in item.seg_indexes:
                # class SegmentsShardTuple(Codable, JsonSerde):
                #     shard_index: ShardIndex
                #     shard: SegmentShard
                response.append(seg_shards[index].shard)

        ack = self._prefix.encode() + response.encode()
        server.stream_and_close(stream_id, ack)

    def client_intercept(self, node: Node, buffer: bytes, stream_id: int) -> Response:
        response, _ = Response.decode_from(buffer)
        response = cast(Response, response)
        logger.info(f"Received CE139 shard response: {response}")

        return response