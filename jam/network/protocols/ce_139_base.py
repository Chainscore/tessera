from dataclasses import dataclass
from typing import cast

from jam.config.logging import logger
from jam.network.quic import QuicServerProtocol
from jam.types.base.integers import Int
from jam.types.base.sequences.bytes.byte_array import ByteArray12
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.work.manifest import SegmentIndex
from jam.types.work.shard import ShardIndex, SegmentShard

from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.utils.json import JsonSerde

from jam.types.protocol.core import ErasureRoot
from jam.types.base.sequences.vector import decodable_vector, Vector


@decodable_vector(SegmentIndex)
class SegmentIndexes(Vector[SegmentIndex]):
    ...

@decodable_dataclass
@dataclass
class ShardRequest(Codable, JsonSerde):
    erasure_root : ErasureRoot
    shard_Index: ShardIndex
    length : Int
    seg_indexes : SegmentIndexes


@decodable_vector(Bytes)
class Justification(Vector[Bytes]):
    ...

@decodable_vector(Justification)
class Justifications(Vector[Justification]):
    ...

@decodable_vector(SegmentShard)
class Response(Vector[SegmentShard]):
    ...


@decodable_dataclass
@dataclass
class ShardsWithJustifications(Codable, JsonSerde):
    shards: Response
    justifications: Justifications


@decodable_vector(ShardRequest)
class CE139Data(Vector[ShardRequest]):
    ...



class SegmentShardRequestBase(NetworkProtocol):

    from jam.network.node import Node

    def __init__(self, prefix: PrefixType):
        super().__init__()
        self._prefix = prefix

    def transmit(self, node: Node, data: CE139Data):
        logger.info(f"Sending segment shard request with prefix {self._prefix}")
        stream = self._prefix.encode() + data.encode()

        responses = Vector([])
        for client in node.connections:
            data = client.stream_and_close(message=stream)
            responses.append(data)

        return data

    @staticmethod
    def parse_request(buffer: bytes) -> CE139Data:
        data, _ = CE139Data.decode_from(buffer)
        shard_request = cast(CE139Data, data)
        return shard_request

    def server_intercept(self, node: Node, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        ...

    def client_intercept(self, node: Node, buffer: bytes, stream_id: int):
        ...
