from jam.config.settings import settings
from jam.network.protocols.ce_139_base import SegmentShardRequestBase, ShardWithJustification, JustifiedResponse
from typing import cast

from jam.config.logging import logger
from jam.merklization import BMRFunctions
from jam.network.quic import QuicServerProtocol
from jam.storage.db.kv import KVStore
from jam.types.base import Vector
from jam.types.base.integers import Int

from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.work.shard import SegmentsShard, BundleShards, BundleShard

from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.work_package.stores.audits import AuditShardsDA
from jam.work_package.stores.mappings import ErasureShardsMap
from jam.work_package.stores.segments import SegmentShardsDA

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
        response = JustifiedResponse([])
        merkle = BMRFunctions()
        for item in request:
            ss_key = er_shards_db.get_ss_root(root=item.erasure_root, shard_index=item.shard_Index)
            db_bs_hash = er_shards_db.get_bs_hashes(root=item.erasure_root)

            # all segment shard at given shard_index
            segs_shard: SegmentsShard = ss_da.get(root=ss_key.segment_shard_root)[0]

            bs_hash = Vector()
            for key in db_bs_hash:
                bs_hash.append(key.bundle_shard_hash)

            # extracting segments shard for given segment index and appending them along with their justification in response data
            for index in item.seg_indexes:
                justify = merkle.trace_fn(values=segs_shard, index=int(index))
                justify.extend(bs_hash)
                item_res = ShardWithJustification(shards=segs_shard[index], justifications=justify)
                response.append(item_res)

        ack = self._prefix.encode() + response.encode()
        server.stream_and_close(stream_id, ack)

    def client_intercept(self, node: Node, buffer: bytes, stream_id: int) -> JustifiedResponse:
        response, _ = JustifiedResponse.decode_from(buffer)
        response = cast(JustifiedResponse, response)
        logger.info(f"client response: {response}")
        logger.info("Received CE140 shard+justification response")

        return response