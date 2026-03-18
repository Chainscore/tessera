import asyncio
from typing import cast
from tsrkit_types import TypedVector, Uint, structure, Choice, U8

from jam.utils.gather import gather_with_exceptions
from jam.utils.task_utils import create_safe_task

from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.connection import PeerConnection
from jam.types.protocol.core import CoreIndex, ValidatorIndex, TrancheIndex
from jam.types.protocol.crypto import (
    HeaderHash,
    BandersnatchVrfSignature,
    Ed25519Signature,
    WorkReportHash,
)

@structure
class CoreReportHash:
    core_index: CoreIndex
    report_hash: WorkReportHash


@structure
class Announcement:
    assigned_reports: TypedVector[CoreReportHash]
    ed25519_signature: Ed25519Signature


@structure
class FirstTrancheEvidence:
    bandersnatch_signature: BandersnatchVrfSignature


@structure
class NoShow:
    validator_index: ValidatorIndex
    announcement: Announcement


NoShows = TypedVector[NoShow]


@structure
class SubsequentTrancheEvidence:
    bandersnatch_signature: BandersnatchVrfSignature
    no_shows: TypedVector[NoShow]


@structure
class TrancheAnnouncement:
    header_hash: HeaderHash
    tranche: TrancheIndex
    announcement: Announcement


class Evidence(Choice):
    first_tranche: FirstTrancheEvidence
    subsequent_tranche: TypedVector[SubsequentTrancheEvidence]


@structure
class CE144Data:
    len_a: Uint[32]
    tranche_announcement: TrancheAnnouncement
    len_b: Uint[32]
    evidence: Evidence

    @property
    def is_valid(self):
        if (
            len(self.tranche_announcement.encode()) == self.len_a
            and len(self.evidence.encode()) == self.len_b
        ):
            return True
        return False


class AuditAnnouncement(NetworkProtocol):
    """
    CE 144 Protocol (Audit announcement) => Announcement of requirement to audit.

    Protocol Flow:
        Auditor -> Auditor

        --> Header_Hash ++ Tranche ++ Announcement[len++[ core_index ++ work_report_hash ] ++ Ed25519_signature]
        --> Evidence[choice[FirstTrancheEvidence, SubsequentTrancheEvidence]]
        --> FIN
        <-- FIN

    sources:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-144-audit-announcement
    """

    _prefix = PrefixType.CE144

    async def transmit(self, data: CE144Data):
        """Transmit Announcement of assign Work report for auditing from Auditor to Other Validators(Auditors)"""

        node = self.jam.router.node

        len_a = data.len_a.encode()
        msg_a = data.tranche_announcement.encode()
        len_b = data.len_b.encode()
        msg_b = data.evidence.encode()

        peers = node.all_connected

        self.logger.info(
            f"Transmitting Work-report Announcement to other Auditors",
            announcement=data.tranche_announcement,
            evidence=data.evidence,
            stream_a_size=data.len_a,
            stream_b_size=data.len_b,
            count=len(peers)
        )

        tasks = []

        for client in peers:
            try:
                self.logger.trace("Transmitting Announcement to", peer=client)

                # send protocol prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # set prefix and buffer
                client.stream_prefix[stream_id] = U8(self._prefix)
                client.stream_buffer[stream_id] = b""

            except Exception as e:
                self.logger.error(
                    "Failed to initialize stream for client",
                    peer=client,
                    error=str(e),
                    exc_info=True,
                )
                continue

            try:
                # send message with their length
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                client.stream_and_keep_open(message=msg_a, stream_id=stream_id)
                client.stream_and_keep_open(message=len_b, stream_id=stream_id)

                res = client.close_and_wait(message=msg_b, stream_id=stream_id)
                task = asyncio.create_task(res)
                tasks.append(task)

                self.logger.debug(
                    "Assign Work Reports announcement transmitted successfully",
                    stream_id=stream_id,
                    port=client.port,
                    validator=client,
                )
            except Exception as e:
                self.logger.error(
                    "Failed to transmitting Announcement",
                    error=str(e),
                    error_type=type(e).__name__,
                )

        responses = await gather_with_exceptions(tasks)

        return responses

    async def req_intercept(self, stream_id: int, server: PeerConnection):
        """Intercept lost of Work Report Announcement from other Auditors for their assigned Work Reports"""
        from jam.storage.tranche_audit_store import tranche_store
        from jam.types.audit.audit_tranche import Tranche

        buffer = server.stream_buffer[stream_id][1:]

        if not buffer:
            self.logger.warning("Empty buffer in req_intercept", stream_id=stream_id, server=server)
            return

        try:
            data = CE144Data.decode(buffer)
            data = cast(CE144Data, data)

            self.logger.debug(
                f"Received Audit's Announcement from other Auditors {server.validator_index}",
                stream_id=stream_id,
                peer=server,
                buffer_size=len(buffer),
                data=data,
            )

        except Exception as e:
            # explicit decode error handling
            server.stop_stream(stream_id, 1)
            self.logger.error(
                "Failed to decode CE144Data",
                stream_id=stream_id,
                server=server,
                error=str(e),
                exc_info=True,
            )
            return

        try:
            v_index = server.validator_index
            tranche_idx = data.tranche_announcement.tranche
            header_hash = data.tranche_announcement.header_hash
            announcements = data.tranche_announcement.announcement

            tranche = Tranche(tranche_index=tranche_idx, header_hash=header_hash)

            # SAVE ANNOUNCEMENT RECORDS
            create_safe_task(
                tranche_store.records_announcement(
                    tranche=tranche, validator_index=v_index, announce=announcements
                ),
                name="record_announcement"
            )

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            ack = b""
            server.stream_and_close(ack, stream_id)
            self.logger.debug(
                "Processed audit announcement",
                server=server,
                stream_id=stream_id,
                validator_index=v_index,
            )

        except NetworkingError as ne:
            server.stop_stream(stream_id, 1)
            self.logger.error(
                "Networking error while handling announcement", error=str(ne), exc_info=True
            )
        except Exception as ex:
            server.stop_stream(stream_id, 1)
            self.logger.error("Unexpected error in req_intercept", error=str(ex), exc_info=True)

    async def res_intercept(self, stream_id: int, client: PeerConnection):
        """Intercept Announcement Acknowledgement"""
        buffer = client.stream_buffer[stream_id]

        if buffer == b"":
            self.logger.debug(
                "Announcement acknowledge received",
                client_index=client.validator_index,
                stream_id=stream_id,
                buffer_size=len(buffer),
            )
            return True

        return False
