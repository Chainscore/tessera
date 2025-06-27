from venv import logger

from typing import cast, TYPE_CHECKING

if TYPE_CHECKING:
    from jam.network.node import Node
from tsrkit_types import TypedVector, Option, Uint, structure, Null
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.quic import QuicProtocol
from jam.types.protocol.core import CoreIndex, ValidatorIndex
from tsrkit_types import U8, Vector
from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature, BandersnatchVrfSignature, HeaderHash
from jam.config.logging import logger
from typing import cast
from jam.work_package.processor import Processor
from jam.network.protocols.ce_138 import CE138Data
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from typing import List, Tuple
from jam.work_package.processor import Processor



@structure
class Announcement:
    assigned_report: List[Tuple[CoreIndex, WorkReportHash]]
    ed25519_signature: Ed25519Signature

@structure
class FirstTrancheEvidence:
    bandersnatch_signature : BandersnatchVrfSignature

@structure
class NoShow:
    validator_index : ValidatorIndex
    Announcement : Announcement

@structure
class SubsequentTrancheEvidence:
    bandersnatch_signature : BandersnatchVrfSignature
    no_show : NoShow

@structure
class Transmit:
    header_hash : HeaderHash
    tranches : U8
    announcement : Announcement

@structure
class CE144data:
    len_a: Uint[32]
    transmit : Transmit
    len_b : Uint[32]
    def __init__(self, tranche):
        if tranche == 0:
            self.Evidence = FirstTrancheEvidence
        else:
            self.Evidence = SubsequentTrancheEvidence

    @property
    def is_valid(self):
        if len(self.transmit.encode()) == self.len_a and len(self.Evidence.encode()) == self.len_b:
            return True
        return False


class AuditAnnouncement(NetworkProtocol):
    """
    CE 144 Protocol (Audit announcement ) => Announcement of requirement to audit.

    Protocol Flow:
        Auditor -> Auditor

        --> Header_Hash ++ Tranche ++ Announcement[len++[ core_index ++ work_report_hash ] ++ Ed25519_signature]
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

        try:
            mes_a = data.transmit.encode()
            len_a = data.len_a.encode()
            mes_b = data.Evidence.encode()
            len_b = data.len_b.encode()
        except Exception as e:
            print("error transmit", e)
            raise

        logger.info(
            "Transmitting announcement of work packages to"
        )

        transmitted_count = 0
        responses = TypedVector([])
        stream_a = self._prefix.encode() + data.transmit.encode()
            stream_b = data.Evidence.encode()

            responses = Vector([])
            for peer in node.peer_conn:
                if int(peer.data.metadata.port) == 40001:
                    logger.info("sending announcement to other validators")
                    client = node.peer_conn[peer][1]
                    stream_id = client.stream_and_keep_open(message=stream_a)
                    data = await client.stream_and_close(message=stream_b, stream_id=stream_id)
                    responses.append(data)

            return responses

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        node = server.node
        buffer = server.stream_buffer[stream_id]

        logger.info("Receive Work report announce,")
        data, offset = CE144data.decode_from(buffer[1:])
        data = cast(CE144data, data)

        if not data.is_valid:
            raise NetworkingError


        # TODO: Extract report
        get_report = data.transmit.announcement.work_report_hash

        # TODO: Request Audit shard request
        shard_request = CE138Data()


    def res_intercept(self, stream_id: int, client: "QuicProtocol"):
        ...