from typing import cast, Tuple

from dataclasses import dataclass
from jam.config.logging import logger
from jam.config.settings import settings
from jam.storage.db.kv import KVStore
from jam.network.quic.server import QuicServerProtocol

from jam.types.base.sequences.bytes import Bytes
from jam.types.base.sequences.vector import Vector
from jam.types.protocol.core import ErasureRoot
from jam.types.protocol.crypto import Hash
from jam.types.work.manifest import Segment
from jam.types.work.shard import SegmentsShard, ShardIndex, BundleShard

from jam.utils.json import JsonSerde
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass

from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.merklization import BMRFunctions

from jam.work_package.stores.mappings import ErasureShardsMap
from jam.work_package.stores.audits import AuditShardsDA, JustificationsDA
from jam.work_package.stores.segments import SegmentShardsDA


@decodable_dataclass
@dataclass
class CE138TransmitData(Codable, JsonSerde):
    erasure_root: ErasureRoot
    shard_index: ShardIndex

@decodable_dataclass
@dataclass
class CE138InterceptData(Codable, JsonSerde):
    bundle_shard: BundleShard
    justification: Bytes


class AuditShardRequestProtocol(NetworkProtocol):
    """
        CE 138 Protocol for Audit shard request

        Auditor -> Assurer

        --> Erasure-Root ++ Shard Index
        --> FIN
        <-- Bundle Shard
        <-- Justification
        <-- FIN

        Source:
            https://docs.jamcha.in/advanced/simple-networking/spec#ce-138-shard-distribution
    """

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE138

    def transmit(self, node: Node, data:CE138TransmitData):
        """Transmit Erasure-Root and Shard Index from Auditor (client) to Assurer (server)"""

        stream_a = self._prefix.encode() + data.erasure_root.encode()
        stream_b = data.shard_index.encode()

        logger.info(f"Transmitting shard index & erasure root to {len(node.connections)} assurer")

        responses = Vector([])
        for client in node.connections:
            stream_id = client.stream_and_keep_open(message=stream_a)
            data = client.stream_and_close(message=stream_b, stream_id=stream_id)
            responses.append(data)

        return responses

    def server_intercept(self, node: Node, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        """Intercept & Process Erasure-Root and Shard Index on Assurer (server)"""

        logger.info("Received Shard index & erasure root")
        data, offset = CE138TransmitData.decode_from(buffer)
        data = cast(CE138TransmitData, data)

        logger.info("Processing")
        # TODO: Process received erasure code & shard index

        d3l = settings.d3l
        audit = settings.audit

        bs_da = ErasureShardsMap(d3l)
        audits_da = AuditShardsDA(audit)
        ss_da = SegmentShardsDA(d3l)
        justification_da = JustificationsDA(audit)

        bundle_shard_hash = bs_da.get_bs_hash(data.erasure_root, data.shard_index).bundle_shard_hash

        bundle_shard = audits_da.get(bs_hash=bundle_shard_hash)[0]

        segment_shard_root = bs_da.get_ss_root(data.erasure_root, data.shard_index)

        justification_ce137 = justification_da.get(data.erasure_root)

        justification = justification_ce137 + segment_shard_root

        stream_a = self._prefix.encode() + bundle_shard.encode()
        stream_b = justification.encode()
        server.stream_and_keep_open(stream_id, stream_a)
        server.stream_and_close(stream_id, stream_b)

    def client_intercept(self, node: Node, buffer: bytes, stream_id: int) -> Tuple[BundleShard, Bytes]:
        """Intercept Bundle Shard and Justification"""

        logger.info("Data received on Auditor Node")
        data, offset = CE138InterceptData.decode_from(buffer)
        data = cast(CE138InterceptData, data)

        # TODO: move this verification part to outside this client_intercept as we dont have shard_index and erasure_root here
        # bmr = BMRFunctions()
        # TODO: Get segment shards received from CE-137 to generate segment shard root for justification
        # segment_shard_root = bmr.wb_merkle_fn(Vector([Bytes(segment_shard)]))
        # bundle_shard_hash = hashlib.blake2b(bytes(data.bundle_shard))
        # s = Vector([ bundle_shard_hash, segment_shard_root])

        # root = bmr.verify_proof(data.justification, s, shard_index)

        # if root == erasure_root:
        # #TODO: save the justification for CE139/140 and proceed further with data
        # else:
        # #TODO: Discard the data

        logger.info("Received bundle shard")
        return data.bundle_shard, data.justification

