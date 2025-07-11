import asyncio
from typing import cast, TYPE_CHECKING

from jam.utils.gather import gather_with_exceptions

if TYPE_CHECKING:
    from jam.network.node import Node

from jam.logging import get_logger

from tsrkit_types import TypedVector, Option, Uint, structure, Null
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.quic import QuicProtocol
from jam.types.protocol.core import CoreIndex, ValidatorIndex
from tsrkit_types import U8, Vector
from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature, BandersnatchVrfSignature, HeaderHash
from jam.types.work.report import WorkReport
from typing import cast
from jam.network.protocols.ce_138 import CE138Data
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from typing import Tuple

# Module-specific logger
logger = get_logger("network")

@structure
class Announcement:
    assigned_report: TypedVector[Tuple[CoreIndex, WorkReportHash]]
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
class CE144Data:
    len_a: Uint[32]
    tranche_announcement : Transmit
    len_b : Uint[32]
    evidence : FirstTrancheEvidence
    # ecvvidance : FirstTrancheEvidence | SubsequentTrancheEvidence
    # def __init__(self, tranche):
    #     if tranche == 0:
    #         self.evidence = FirstTrancheEvidence
    #     else:
    #         self.evidence = SubsequentTrancheEvidence

    @property
    def is_valid(self):
        if len(self.tranche_announcement.encode()) == self.len_a and len(self.evidence.encode()) == self.len_b:
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

    async def transmit(self, node: Node, data: CE144Data):

        msg_a = data.tranche_announcement.encode()
        len_a = data.len_a.encode()
        msg_b = data.evidence.encode()
        len_b = data.len_b.encode()

        logger.info(
            f"Transmitting data",
            announcement=data.tranche_announcement.announcement,
            evidence=data.evidence.bandersnatch_signature,
            stream_a_size=data.len_a,
            stream_b_size=data.len_b,
        )

        tasks = []
        responses = []
        transmitted_count = 0

        try:
            for peer in node.peer_conn:

                logger.info(f"Transmitting Work package's announcement to {len(node.peer_conn)} validators ")

                client = node.peer_conn[peer][1]

                # send protocol prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

                transmitted_count += 1

                # send message with their length
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                client.stream_and_keep_open(message=msg_a, stream_id=stream_id)
                client.stream_and_keep_open(message=len_b, stream_id=stream_id)

                res =  await client.close_and_wait(message=msg_b, stream_id=stream_id)
                task = asyncio.create_task(res)
                tasks.append(task)

                responses = await gather_with_exceptions(tasks)

                logger.info(
                    "Transmitted announcement to validator",
                    stream_id=stream_id,
                    port=peer.port,
                )

        except Exception as e:
            logger.error(
                "failed to transmit audit announcement",
                error=str(e),
                error_type=type(e).__name__
            )

        return responses


    def req_intercept(self, stream_id: int, server: QuicProtocol):

        buffer = server.stream_buffer[stream_id]

        data, offset = CE144Data.decode_from(buffer[1:])
        data = cast(CE144Data, data)
        try:
            logger.debug(
                "Received announcement for auditing",
                stream_id=stream_id,
                peer=server.peer,
                buffer_size=len(buffer[1:])
            )


            if not data.is_valid:
                raise NetworkingError

            # TODO: Extract report
            get_report = data.tranche_announcement.announcement.work_report_hash

            # TODO: Request Audit shard request
            # shard_request = CE138Data()

            ack= b""
            server.stream_and_close(ack, stream_id)


        except Exception as e:
            # stop streaming
            server.stop_stream(stream_id, 1)


    def res_intercept(self, stream_id: int, client: "QuicProtocol"):
        buffer = client.stream_buffer[stream_id]
        if buffer[1:] == b"":
            logger.info(
                "Assurance ack received",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )
            return True

        return False
