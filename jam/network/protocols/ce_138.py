import hashlib
from typing import cast, Tuple

from dataclasses import dataclass
from jam.config.logging import logger
from jam.types import Vector
from jam.network.quic.server import QuicServerProtocol
from jam.types.base.sequences.bytes import Bytes
from jam.types.protocol.core import ErasureRoot
from jam.types.work.manifest import Segment, Justification
from jam.types.work.shard import SegmentsShard, ShardIndex, BundleShard

from jam.utils.json import JsonSerde
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass

from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.types.base.sequences.bytes.byte_array import ByteArray
from jam.merklization import BMRFunctions


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
        bundle_shard = ByteArray('3b8987132d58aea08ec55247fd64436c3a553e3ab42260c6a31bf27931ee2cba868d4c59b626fb1d365fa5cb0edd5f1e2d72b7d6d7998ad0995314ad9eee86c3')

        # TODO: Get segment shards received from CE-137 to generate segment shard root for justification
        segment_shard = SegmentsShard([
            Segment('8a84add96a80d1566e789df3'),
            Segment('1162d08611b468d38af07ca5'),
            Segment('3810e996013e0c0a8abe11de'),
            Segment('68b95e1999bc5864308a7c68'),
            Segment('fc12fb3db7a24b0b52fb57f6'),
        ])

        bundle_shard_hash = hashlib.blake2b(bytes(bundle_shard))

        bmr = BMRFunctions()
        segment_shard_root = bmr.wb_merkle_fn(Vector([Bytes(segment_shard)]))

        s = Vector([ bundle_shard_hash, segment_shard_root])

        justification = bmr.trace_fn(values=s, index=int(data.shard_index))

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

