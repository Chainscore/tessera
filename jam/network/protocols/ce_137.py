from typing import cast, Tuple

from dataclasses import dataclass
from jam.config.logging import logger
from jam.types import Vector
from jam.network.quic.server import QuicServerProtocol

from jam.merklization import BMRFunctions
from jam.types.protocol.crypto import Hash
from jam.types.protocol.core import ErasureRoot
from jam.types.work.manifest import Justification
from jam.types.work.shard import BundleShard, SegmentsShard, SegmentShard, ShardIndex

from jam.utils.json import JsonSerde
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass

from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.types.base.sequences.bytes.byte_array import ByteArray

@decodable_dataclass
@dataclass
class CE137TransmitData(Codable, JsonSerde):
    erasure_root: ErasureRoot
    shard_index: ShardIndex

@decodable_dataclass
@dataclass
class CE137InterceptData(Codable, JsonSerde):
    bundle_shard: BundleShard
    segment_shard: SegmentsShard
    justification: Justification


class ShardDistributionProtocol(NetworkProtocol):
    """
        CE 137 Protocol for shard distribution

        Assurer -> Guarantor

        --> Erasure-Root ++ Shard Index
        --> FIN
        <-- Bundle Shard
        <-- [Segment Shard] (Should include all exported and proof segment shards with the given index)
        <-- Justification
        <-- FIN

        Source:
            https://docs.jamcha.in/advanced/simple-networking/spec#ce-137-shard-distribution
    """

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE137

    async def transmit(self, node: Node, data:CE137TransmitData):
        """Transmit Erasure-Root and Shard Index from Assurer (client) to Guarantor (server)"""

        stream_a = self._prefix.encode() + data.erasure_root.encode()
        stream_b = data.shard_index.encode()

        logger.info(f"Transmitting shard index & erasure root to {len(node.connections)} guarantors")

        for client in node.connections:
            stream_id = client.stream_and_keep_open(message=stream_a)
            data = await client.stream_and_close(message=stream_b, stream_id=stream_id)

            if data is not None:
                return data

    def server_intercept(self, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        """Intercept & Process Erasure-Root and Shard Index on Guarantor (server)"""

        logger.info("Received Shard index & erasure root")
        data, offset = CE137TransmitData.decode_from(buffer)
        data = cast(CE137TransmitData, data)

        logger.info("Processing")
        # TODO: Process received erasure root & shard index

        bundle_shard = BundleShard('3b8987132d58aea08ec55247fd64436c3a553e3ab42260c6a31bf27931ee2cba868d4c59b626fb1d365fa5cb0edd5f1e2d72b7d6d7998ad0995314ad9eee86c3')

        segment_shard_root = ByteArray('3b8987132d58aea08ec55247fd64436c3a553e3ab42260c6a31bf27931ee2cba868d4c59b626fb1d365fa5cb0edd5f1e2d72b7d6d7998ad0995314ad9eee86c3')

        segment_shard = SegmentsShard([
                         SegmentShard('8a84add96a80d1566e789df3'),
                         SegmentShard('1162d08611b468d38af07ca5'),
                         SegmentShard('3810e996013e0c0a8abe11de'),
                         SegmentShard('68b95e1999bc5864308a7c68'),
                         SegmentShard('fc12fb3db7a24b0b52fb57f6'),
                        ])

        bundle_shard_hash = Hash.blake2b(bundle_shard.encode())
        s = Vector([ bundle_shard_hash, segment_shard_root])

        bmr = BMRFunctions()
        justification = bmr.trace_fn(values=s, index=int(data.shard_index))

        stream_a = self._prefix.encode() + bundle_shard.encode()
        stream_b = segment_shard.encode()
        stream_c = justification.encode()

        server.stream_and_keep_open(stream_id, stream_a)
        server.stream_and_keep_open(stream_id, stream_b)
        server.stream_and_close(stream_id, stream_c)

    def client_intercept(self, buffer: bytes, stream_id: int) -> Tuple[BundleShard, SegmentsShard, Justification] | None:
        """Intercept Bundle Shard, [Segment Shard] and Justification"""

        logger.info("Data received on Assurer Node")
        data, offset = CE137InterceptData.decode_from(buffer)
        data = cast(CE137InterceptData, data)

        # TODO: move this verification part to outside this client_intercept as we dont have shard_index and erasure_root here
        # bmr = BMRFunctions()
        # segment_shard_root = bmr.wb_merkle_fn(Vector([Bytes(data.segment_shard)]))
        # bundle_shard_hash = hashlib.blake2b(bytes(data.bundle_shard))
        # s = Vector([ bundle_shard_hash, segment_shard_root])
        #
        # root = bmr.verify_proof(data.justification, s, shard_index)
        #
        # if root == erasure_root:
        # #TODO: save the justification for CE139/140 and proceed further with data
        # else:
        # #TODO: Discard the data

        logger.info("Received bundle shard and segment shard")
        if data:
            return data.bundle_shard, data.segment_shard, data.justification
        else:
            return None
