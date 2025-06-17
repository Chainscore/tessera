from jam.config.settings import settings
from jam.network.protocols.ce_139_base import SegmentShardRequestBase, ShardsWithJustifications, Justifications, Response
from typing import cast

from jam.config.logging import logger
from jam.merklization import BMRFunctions
from jam.network.quic import QuicServerProtocol
from jam.types.base import Vector

from jam.types.work.shard import SegmentsShard, SegmentShard

from jam.network.protocols.base import PrefixType
from jam.work_package.stores.mappings import ErasureShardsMap
from jam.work_package.stores.segments import SegmentShardsDA


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
    from jam.network.node import Node

    def __init__(self):
        super().__init__(PrefixType.CE140)

    def server_intercept(self, node: Node, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        request = self.parse_request(buffer)
        logger.info("Handling CE140 shard + justification request")
        d3l = settings.d3l

        er_shards_db = ErasureShardsMap(d3l)
        ss_da = SegmentShardsDA(d3l)

        # Fetching segments...
        response = Response([])
        justifications = Justifications([])
        merkle = BMRFunctions()
        for item in request:
            ss_key = er_shards_db.get_ss_root(root=item.erasure_root, shard_index=item.shard_Index)
            db_bs_hash = er_shards_db.get_bs_hashes(root=item.erasure_root)

            # all segment shard at given shard_index with segment index
            segs_shard_segment_index: SegmentsShard = ss_da.get(root=ss_key.segment_shard_root)[0]

            # all segment shard at given shard_index
            segs_shards: Vector[SegmentShard] = Vector([])
            for segs_shard in segs_shard_segment_index:
                segs_shards.append(segs_shard.shard)

            # segs_shard: SegmentsShard = ss_da.get(root=ss_key.segment_shard_root)[0]

            bs_hash = Vector([])
            for key in db_bs_hash:
                bs_hash.append(key.bundle_shard_hash)

            # extracting segments shard for given segment index and appending them along with their justification in response data
            for index in item.seg_indexes:
                justify = merkle.trace_fn(values=segs_shards, index=int(index))
                justify.extend(bs_hash)
                response.append(segs_shards[index])
                justifications.append(justify)

        ack = self._prefix.encode() + response.encode()
        stream_id = server.stream_and_keep_open(stream_id, ack)
        ack = self._prefix.encode() + justifications.encode()
        server.stream_and_close(stream_id, ack)

    def client_intercept(self, node: Node, buffer: bytes, stream_id: int) -> ShardsWithJustifications:
        response, _ = ShardsWithJustifications.decode_from(buffer)
        response = cast(ShardsWithJustifications, response)
        logger.info(f"client response: {response}")
        logger.info("Received CE140 shard+justification response")

        return response