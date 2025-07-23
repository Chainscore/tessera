import asyncio
from typing import cast, TYPE_CHECKING, Tuple
from wsgiref.validate import validator

from jam.utils.gather import gather_with_exceptions

if TYPE_CHECKING:
    from jam.network.node import Node

from jam.logging import get_logger
from tsrkit_types import TypedVector, Uint, structure, Choice
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.quic import QuicProtocol
from jam.types.protocol.core import CoreIndex, ValidatorIndex,TrancheIndex
from tsrkit_types import U8
from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature, BandersnatchVrfSignature, HeaderHash
from typing import cast
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code


# Module-specific logger
logger = get_logger("network")

@structure
class Assign:
    core_index: CoreIndex
    report_hash: WorkReportHash

@structure
class Announcement:
    assigned_report: TypedVector[Assign]
    ed25519_signature: Ed25519Signature

@structure
class FirstTrancheEvidence:
    bandersnatch_signature : BandersnatchVrfSignature

@structure
class NoShow:
    validator_index : ValidatorIndex
    announcement : Announcement

@structure
class SubsequentTrancheEvidence:
    bandersnatch_signature : BandersnatchVrfSignature
    no_show : NoShow

@structure
class Transmit:
    header_hash : HeaderHash
    tranches : U8
    announcement : Announcement

class Evidence(Choice):
    first_tranche: FirstTrancheEvidence
    Subsequent_tranche : SubsequentTrancheEvidence

@structure
class CE144Data:
    len_a: Uint[32]
    tranche_announcement : Transmit
    len_b : Uint[32]
    evidence : Evidence

    @property
    def is_valid(self):
        if len(self.tranche_announcement.encode()) == self.len_a and len(self.evidence.encode()) == self.len_b:
            return True
        return False


class AuditAnnouncement(NetworkProtocol):
    """
    CE 144 Protocol (Audit announcement) => Announcement of requirement to audit.

    Protocol Flow:
        Auditor -> Auditor

        -->import asyncio
 Header_Hash ++ Tranche ++ Announcement[len++[ core_index ++ work_report_hash ] ++ Ed25519_signature]
        --> Evidence[choice[FirstTrancheEvidence, SubsequentTrancheEvidence]]
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
        """ Transmit Announcement of assign Work report for auditing from Auditor to Other Validators(Auditors) """

        len_a = data.len_a.encode()
        msg_a = data.tranche_announcement.encode()
        len_b = data.len_b.encode()
        msg_b = data.evidence.encode()

        logger.info(
            f"Transmitting Announcement to other Auditors",
            announcement=data.tranche_announcement,
            evidence=data.evidence,
            stream_a_size=data.len_a,
            stream_b_size=data.len_b,
        )

        tasks = []
        responses = []
        transmitted_count = 0

        try:
            logger.info(f"Transmitting Work report's announcement to {len(node.peer_conn)} validators ")

            for peer in node.peer_conn:
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

                res = client.close_and_wait(message=msg_b, stream_id=stream_id)
                task = asyncio.create_task(res)
                tasks.append(task)

                logger.debug(
                    "Transmitted announcement",
                    stream_id=stream_id,
                    port=peer.port,
                    validator=peer
                )

            responses = await gather_with_exceptions(tasks)

        except Exception as e:
            logger.error(
                "Failed to transmitting Announcement",
                error=str(e),
                error_type=type(e).__name__
            )


        return responses

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """ Intercept lost of Work Report Announcement from other Auditors for their assigned Work Reports"""
        from jam.operations.tranche_store import tranche_store, Tranche

        v_r: dict[ValidatorIndex, set[WorkReportHash]] = {}

        buffer = server.stream_buffer[stream_id]

        try:
            data, offset = CE144Data.decode_from(buffer[1:])
            data = cast(CE144Data, data)

            get_v_assign = data.tranche_announcement.announcement.assigned_report
            v_index = server.peer.peer_index
            tranche_idx = data.tranche_announcement.tranches
            header_hash = data.tranche_announcement.header_hash

            v_r[v_index] = {assign.report_hash for assign in get_v_assign}

            tranche = Tranche(
                tranche_index= tranche_idx,
                header_hash=header_hash
            )

            for v, r_hash in v_r.items():
                for value in r_hash:
                    # print(value, tranche ,v_index)
                    tranche_store.add_announce(tranche=tranche, wr_hash=value, validator_index=v_index)


            logger.debug(
                "Received Audit's Announcement from other Auditors",
                stream_id=stream_id,
                peer=server.peer,
                buffer_size=len(buffer[1:])
            )

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            ack= b""
            server.stream_and_close(ack, stream_id)

        except Exception as e:
            # Stop Streaming
            server.stop_stream(stream_id, 1)

            logger.error(
                "Error while intercepting Audit's Announcement",
                auditor=server.peer,
                stream_id=stream_id,
                error=str(e),
                err_type=type(e).__name__,
            )

    def res_intercept(self, stream_id: int, client: "QuicProtocol"):
        """ Intercept Announcement Acknowledgement """
        buffer = client.stream_buffer[stream_id]
        if buffer[1:] == b"":
            logger.info(
                "Announcement acknowledge received",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )
            return True

        return False
