from dataclasses import dataclass
from typing import cast

from jam.config.logging import logger
from jam.network.quic import QuicServerProtocol
from jam.types import ByteArray32
from jam.types.base.integers import Int
from jam.types.base.integers.fixed import U16
from jam.types.base.sequences.bytes.byte_array import ByteArray12

from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.utils.json import JsonSerde

from tests.dummy.utils import create_dummy_bytes12, create_dummy_bytes32

from jam.types.protocol.core import ErasureRoot
from jam.types.base.sequences.vector import decodable_vector, Vector


@decodable_vector(Int)
class SegmentIndexes(Vector[Int]):
    ...


@decodable_dataclass
@dataclass
class ShardRequest(Codable, JsonSerde):
    erasure_root : ErasureRoot
    shard_Index: U16
    length : Int
    seg_indexes : SegmentIndexes


@decodable_vector(ByteArray32)
class Justifications(Vector[ByteArray32]):
    ...


@decodable_dataclass
@dataclass
class ShardWithJustification(Codable, JsonSerde):
    shards: ByteArray12
    justifications: Justifications

@decodable_vector(ByteArray12)
class Response(Vector[ByteArray12]):
    ...


@decodable_vector(ShardRequest)
class CE139Data(Vector[ShardRequest]):
    ...


@decodable_vector(ShardWithJustification)
class JustifiedResponse(Vector[ShardWithJustification]):
    ...


class SegmentShardRequestBase(NetworkProtocol):

    from jam.network.node import Node

    def __init__(self, prefix: PrefixType):
        super().__init__()
        self._prefix = prefix

    def transmit(self, node: Node, data: CE139Data):
        logger.info(f"Sending segment shard request with prefix {self._prefix}")
        stream = self._prefix.encode() + data.encode()
        for client in node.connections:
            client.stream_and_close(message=stream)


    def parse_request(self, buffer: bytes) -> CE139Data:
        data, _ = CE139Data.decode_from(buffer)
        shard_request = cast(CE139Data, data)
        print("sharq request data")
        return shard_request

    def server_intercept(self, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        ...

    def client_intercept(self, buffer: bytes, stream_id: int):
        ...


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


class SegmentShardRequestWithJustifications(SegmentShardRequestBase):
    """
        CE 139 Protocol for Requesting Segments Shards from Assurers

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

        response = JustifiedResponse([ShardWithJustification(shards=create_dummy_bytes12(), justifications=Justifications([create_dummy_bytes32()]))])
        ack = self._prefix.encode() + response.encode()
        server.stream_and_close(stream_id, ack)

    def client_intercept(self, buffer: bytes, stream_id: int):
        response, _ = JustifiedResponse.decode_from(buffer)
        response = cast(JustifiedResponse, response)
        logger.info(f"client response: {response}")
        logger.info("Received CE140 shard+justification response")


# class SegmentShardRequest(NetworkProtocol):
#     """
#     CE 139 Protocol for Requesting Segments Shards from Assurers
#
#     Protocol Flow:
#         Guarantor -> Assurers
#
#         --> [Erasure-Root ++ Shard Index ++ len++[Segment Index]]
#         --> FIN
#         <-- [Segment Shard]
#         <-- FIN
#     Source:
#         https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-139140-segment-shard-request
#     """
#
#     from jam.network.node import Node
#
#     def __init__(self):
#         super().__init__()
#         self._prefix = PrefixType.CE134
#
#     def transmit(self, node: Node, data: CE139Data):
#         """Request Segments Shards from Guarantors"""
#
#         logger.info(f"Requesting segments shards from Assurers")
#         # TODO: Use Actual Guarantors Connections
#
#         stream_a = self._prefix.encode() + data.encode()
#
#         for client in node.connections:
#             client.stream_and_close(message=stream_a)
#
#
#     def server_intercept(self, buffer: bytes, server: QuicServerProtocol, stream_id: int):
#         """Intercept Work Package Bundle & Build Work Report on Core's Guarantors (server)"""
#
#         logger.info("Received Segment shard request from Guarantor")
#         data, offset = CE139Data.decode_from(buffer)
#         data = cast(CE139Data, data)
#
#         logger.info("fetching segments shard from DB")
#         # TODO: Fetch Segment Shards stored in the DB and then send back the data to Guarantor
#
#
#         # Return Credential to requesting Guarantor
#         dummy_shard = Response([create_dummy_bytes12()])
#         ack = self._prefix.encode() + dummy_shard.encode()
#         server.stream_and_close(stream_id, ack)
#
#         logger.info("Report's Credential sent back to OG Guarantor")
#
#     def client_intercept(self, buffer: bytes, stream_id: int):
#         """Intercept validated Work Report from guarantors"""
#
#         logger.info(f"Report's Credential received on OG guarantor (client) via stream {stream_id}")
#         data, offset = Response.decode_from(buffer)
#         data = cast(Response, data)
#
#         logger.info("Distributing this Work Report after achieving majority")
#         # TODO: Save Work Report & Check Majority & Distribute
#         # Process goes here