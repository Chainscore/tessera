from venv import logger

from Crypto.SelfTest.IO.test_PKCS8 import clear_key

from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.network.quic import QuicServerProtocol
from jam.types.base import U8, Nullable
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from dataclasses import dataclass
from jam.types.protocol.core import CoreIndex
from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature, BandersnatchVrfSignature, HeaderHash
from jam.utils.json import JsonSerde
from jam.config.logging import logger
from jam.types.base.sequences.vector import Vector
from typing import cast
from jam.types.base.null import Null


@decodable_dataclass
@dataclass
class EvidenceTrancheZero(Codable, JsonSerde):
    bandersnatch_signature : BandersnatchVrfSignature


@decodable_dataclass
@dataclass
class EvidenceTrancheNotZero(Codable, JsonSerde):
    ...


@decodable_dataclass
@dataclass
class Announcement(Codable, JsonSerde):
    core_index: CoreIndex
    work_report_hash: WorkReportHash
    ed25519_signature: Ed25519Signature


@decodable_dataclass
@dataclass
class Transmit(Codable, JsonSerde):
    header_hash : HeaderHash
    tranches : U8
    announcement : Announcement


@decodable_dataclass
@dataclass
class CE144data(Codable, JsonSerde):
    transmit : Transmit
    Evidence : EvidenceTrancheZero


class AuditAnnouncement(NetworkProtocol):
    """
    CE 144 Protocol (Audit announcement ) => Announcement of requirement to audit.

    Protocol Flow:
        Auditor -> Auditor

        --> Header_Hash ++ Tranche ++ Announcement
        --> Evidence
        --> FIN
        <-- FIN

    sources:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-144-audit-announcement
    """
    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE144

    async def transmit(self, node: Node, data: CE144data):
        logger.info(f"Announcement of requirement of audit with evidence =>  {node.connections}")

        # TODO: Use actual Auditor to announcement of auditing to other auditor

        stream_a = self._prefix.encode() + data.transmit.encode()
        stream_b = data.Evidence.encode()

        responses = Vector([])
        for peer in node.peer_conn:
            client = node.peer_conn[peer][1]
            stream_id = client.stream_and_keep_open(message=stream_a)
            data = await client.stream_and_close(message=stream_b, stream_id=stream_id)
            responses.append(data)

        return responses

    def server_intercept(self, node: Node, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        logger.info("Receiving assurance for work report")
        data, offset = CE144data.decode_from(buffer)
        data = cast(CE144data, data)




    def client_intercept(self, node: Node, buffer: bytes, stream_id: int):
        return Null