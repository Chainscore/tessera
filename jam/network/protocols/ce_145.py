import asyncio
import math
from jam.utils.task_utils import create_safe_task
from typing import cast
from tsrkit_types import structure, Uint, U8, U32
from jam.types.protocol.core import ValidatorIndex, EpochIndex
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.connection import PeerConnection
from jam.log_setup import network_logger
from jam.types.protocol.crypto import Ed25519Signature, Ed25519Public
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.utils.gather import gather_with_exceptions
from jam.types.work.report import WorkReportHash
from jam.utils.constants import EPOCH_LENGTH
from jam.types.audit.audit_tranche import Tranche

logger = network_logger


@structure
class Judgment:
    epoch_index: EpochIndex
    validator_index: ValidatorIndex
    validity: Uint[8]
    work_report_hash: WorkReportHash
    ed25519_signature: Ed25519Signature


@structure
class CE145Data:
    len_a: Uint[32]
    judgment: Judgment

    @property
    def is_valid(self):
        if len(self.judgment.encode()) == self.len_a:
            return True
        return False


class JudgmentPublication(NetworkProtocol):
    """
    CE 145 (Judgement Publication) protocol for sharing Judgment to other Auditors.

    Protocol Flow:
        Auditor -> Validator

        --> Epoch_index ++ Validator_Index ++ Validity ++ Work_Report_Hash ++ Ed25519_Signature
        --> FIN
        <-- FIN

    sources:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-145-judgment-publication
    """

    _prefix = PrefixType.CE145

    async def transmit(self, data: CE145Data):
        """Transmit Judgments for the particular Work Report to other Auditors"""
        node = self.jam.router.node

        len_a = data.len_a.encode()
        msg_a = data.judgment.encode()

        tasks = []
        transmitted_count = 0

        peers = node.all_connected

        try:
            self.logger.info(
                f"Transmitting Work-report judgement to other Auditors",
                peers=len(peers),
                judgment=data.judgment,
                judgement_len=data.len_a,
            )

            for client in peers:
                try:
                    # send protocol prefix
                    stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                    # set prefix and buffer
                    client.stream_prefix[stream_id] = U8(self._prefix)
                    client.stream_buffer[stream_id] = b""

                    transmitted_count += 1

                    # send message with their length
                    client.stream_and_keep_open(message=len_a, stream_id=stream_id)

                    res = client.close_and_wait(message=msg_a, stream_id=stream_id)
                    task = asyncio.create_task(res)
                    tasks.append(task)

                    self.logger.debug(
                        "Judgment transmitted successfully",
                        stream_id=stream_id,
                        port=client.port,
                        validator=client,
                    )
                except Exception as e:
                    self.logger.error(
                        "Failed to transmit to client",
                        client=client,
                        error=str(e),
                        exc_info=True,
                    )

            responses = await gather_with_exceptions(tasks)
            return responses

        except Exception as e:
            self.logger.error(
                "Failed to transmitting judgment",
                error=str(e),
                error_type=type(e).__name__,
            )

    async def req_intercept(self, stream_id: int, server: PeerConnection):
        """Intercept individual Judgment from other Auditors for their assigned Work Reports"""
        state = self.jam.state
        settings = self.jam.settings

        buffer = server.stream_buffer[stream_id][1:]

        if not buffer:
            self.logger.warning("Empty buffer in req_intercept", stream_id=stream_id, server=server)
            return

        try:
            data = CE145Data.decode(buffer)
            data = cast(CE145Data, data)

            self.logger.debug(
                f"Received Judgment from auditor {server.validator_index}",
                stream_id=stream_id,
                peer=server,
                buffer_size=len(buffer[1:]),
                data=data,
            )
        except Exception as e:
            server.stop_stream(stream_id, 1)
            self.logger.error(
                "Failed to decode CE145Data",
                stream_id=stream_id,
                server=server,
                error=str(e),
                exc_info=True,
            )
            return

        try:
            # ----------------------- break down judgments properties -----------------
            epoch_index = data.judgment.epoch_index
            validator_index = data.judgment.validator_index
            validity = data.judgment.validity
            wr_hash = data.judgment.work_report_hash
            ed25519_signature = data.judgment.ed25519_signature

            # epoch compare
            val_index = settings.validator_index(state)
            curr_epoch_index = EpochIndex(math.floor(state.tau / EPOCH_LENGTH))
            if curr_epoch_index == epoch_index:
                ed25519_key = state.kappa[val_index].ed25519
                self.logger.info("Same epoch judgment received")
            else:
                if curr_epoch_index - EpochIndex(1) == epoch_index:
                    ed25519_key = state.lambda_[val_index].ed25519
                    self.logger.info("Judgments received for last epoch")
                else:
                    raise KeyError("Judgment age is not valid; work report is too old.")

            # Handling received judgment
            create_safe_task(
                self.handle_judgment(judgment=data.judgment, ed25519_key=ed25519_key),
                name="handle_judgment"
            )

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            ack = b""
            server.stream_and_close(ack, stream_id)

        except Exception as e:
            # Stop Streaming
            server.stop_stream(stream_id, 1)
            self.logger.error(
                "Error while intercepting Judgement",
                auditor=server,
                stream_id=stream_id,
                error=str(e),
                err_type=type(e).__name__,
            )

    async def res_intercept(self, stream_id: int, client: PeerConnection):
        """Intercept judgment Acknowledgement"""
        buffer = client.stream_buffer[stream_id]

        if buffer == b"":
            self.logger.info(
                "Judgment acknowledge received",
                client_index=client.validator_index,
                stream_id=stream_id,
                buffer_size=len(buffer),
            )
            return True

        return False

    async def handle_judgment(self, judgment: Judgment, ed25519_key: Ed25519Public):
        """Find tranche for received work report and if get negative judgments handle it."""
        from jam.storage.tranche_audit_store import tranche_store

        try:
            tranche = await tranche_store.fetch_rep_tranche(judgment)

            if not tranche:
                raise ValueError(f"Tranche not found for report {judgment.work_report_hash.hex()}")

            if judgment.validity == U8(0):
                create_safe_task(
                    self.negative_judgments(judgment=judgment, tranche=tranche),
                    name="handle_judgment"
                )

            await tranche_store.update_judgment(
                tranche=tranche, judgment=judgment, ed25519_public=ed25519_key
            )

        except Exception as JERR:
            logger.error(
                "Error Handling Judgment, fetching tranche for work report",
                judgment=judgment.to_json(),
                err=str(JERR),
                err_type=type(JERR).__name__,
                exc_info=True,
            )

    async def negative_judgments(self, judgment: Judgment, tranche: Tranche):
        """this handle only negative judgments, do refine and transmit judgments."""
        from jam.storage.tranche_audit_store import tranche_store
        from jam.audit.audit import Audit
        from jam.audit.utils import Utils

        state = self.jam.state
        settings = self.jam.settings

        audit = Audit(self.jam)
        utils = Utils(self.jam)

        validator_index = settings.validator_index(state)
        wr_hash = judgment.work_report_hash

        # process refine results
        wr = await utils.fetch_report(wr_hash=wr_hash)
        update_validity = await audit.refine(wr=wr)

        epoch_index = EpochIndex(math.floor(state.tau / EPOCH_LENGTH))

        ed25519_signature = audit.judgment_signature(
            wr_hash=judgment.work_report_hash, validity=update_validity
        )

        judgment = Judgment(
            epoch_index=epoch_index,
            validator_index=validator_index,
            validity=update_validity,
            work_report_hash=judgment.work_report_hash,
            ed25519_signature=Ed25519Signature(ed25519_signature),
        )

        # ------------------- Save judgment in Tranche State ---------------------------------------------
        await tranche_store.update_judgment(
            tranche=tranche, judgment=judgment, ed25519_public=settings.ed25519_public
        )

        data = CE145Data(len_a=U32(len(judgment.encode())), judgment=judgment)
        response = await self.transmit(data=data)
