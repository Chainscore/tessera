from jam.state.state import State
from typing import cast

from dataclasses import dataclass
from jam.config.logging import logger
from jam.types.base.integers import Int
from jam.network.quic.server import QuicServerProtocol

from jam.utils.json import JsonSerde
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass

from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.types.work.package import WorkPackage
from jam.types.base import (
    ByteArray32
)
from jam.types.base.integers import U16
from jam.types.base.sequences.bytes.byte_array import decodable_bytearray, ByteArray

@decodable_bytearray(12)
class ByteArray12(ByteArray):
    ...

@decodable_dataclass
@dataclass
class CE138Data(Codable, JsonSerde):
    Erasure_Root: ByteArray32
    Shard_Index: U16

@decodable_dataclass
@dataclass
class CE138Data2(Codable, JsonSerde):
    Bundle_Shard: ByteArray


class AuditShardRequestProtocol(NetworkProtocol):
    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE138

    def transmit(self, node: Node, data:CE138Data):
        """
        """
        stream_a = self._prefix.encode() + data.Erasure_Root.encode()
        stream_b = data.Shard_Index.encode()

        logger.info(f"Transmitting shard index & erasure root to {len(node.connections)} assurer")

        for client in node.connections:
            stream_id = client.stream_and_keep_open(message=stream_a)
            client.stream_and_close(message=stream_b, stream_id=stream_id)



    @classmethod
    def server_intercept(self, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        """
        """
        logger.info("Received Shard index & erasure root")
        data, offset = CE138Data.decode_from(buffer)
        data = cast(CE138Data, data)

        logger.info("Processing")
        # TODO: Process received erasure code & shard index
        bundle_shard = '3b8987132d58aea08ec55247fd64436c3a553e3ab42260c6a31bf27931ee2cba868d4c59b626fb1d365fa5cb0edd5f1e2d72b7d6d7998ad0995314ad9eee86c3'

        stream_a = self._prefix.encode() + bundle_shard.encode()

        server.stream_and_close(stream_id, stream_a)



    @classmethod
    def client_intercept(self, buffer: bytes, stream_id: int):
        logger.info("Data received on Auditor Node")
        data, offset = CE138Data2.decode_from(buffer)
        data = cast(CE138Data2, data)
        logger.info("Received bundle shard")

