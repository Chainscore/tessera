import asyncio
import math

from typing import cast

from docutils.nodes import header
from flask import Flask
from numpy.ma.core import empty
from tsrkit_types import structure, Uint, Bool, U8, U32

from jam.utils.constants import EPOCH_LENGTH, VALIDATORS_SUPER_MAJORITY
from jam.types.protocol.core import ValidatorIndex, EpochIndex, TrancheIndex

from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.connection import NodeConnection
from jam.logging import get_logger
from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature, HeaderHash

from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.utils.gather import gather_with_exceptions
from jam.types.work.report import WorkReport, WorkReportHash, WorkReports
from jam.block import Block, Header

# Module-specific logger
logger = get_logger("network")


@structure
class Judgment:
    epoch_index: EpochIndex
    validator_index: ValidatorIndex
    validity: Bool
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
    CE 145 (Judgement Publication) protocol for sharing Judgment to other Auditors

    Protocol Flow:
        Auditor -> Validator

        --> Epoch_index ++ Validator_Index ++ Validity ++ Work_Report_Hash ++ Ed25519_Signature
        --> FIN
        <-- FIN

    sources:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-145-judgment-publication

    """

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE145

    async def transmit(self, data: CE145Data):
        """Transmit Judgments for the particular Work Report to other Auditors"""
        from jam.network.start import node
        len_a = data.len_a.encode()
        msg_a = data.judgment.encode()

        logger.info(
            f"Transmitting Work-report judgement",
            judgment=data.judgment,
            len_a=data.len_a
        )

        tasks = []
        transmitted_count = 0

        try:
            logger.info(f"Transmitting Judgment to {len(node.all_connected)} validators")

            for client in node.all_connected:

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

                logger.debug(
                    "Judgment transmitted",
                    stream_id=stream_id,
                    port=client.port,
                    validator=client,
                )
            responses = await gather_with_exceptions(tasks)
            return responses

        except Exception as e:
            logger.error(
                "Failed to transmit judgment",
                error=str(e),
                error_type=type(e).__name__,
            )

    async def req_intercept(self, stream_id: int, server: NodeConnection):
        """Intercept individual Judgment from other Auditors for their assigned Work Reports """
        from jam.storage.tranche_store import tranche_store, Tranche
        from jam.finality.finality import Finality
        from jam.settings import settings
        from jam.audit.auditor import Auditor
        from jam.state.state import state

        auditor = Auditor()

        buffer = server.stream_buffer[stream_id][1:]

        latest_block = Finality.load_latest(kv=settings.main_db)

        try:
            data = CE145Data.decode(buffer)
            data = cast(CE145Data, data)

            # ------------------------- find out tranche -------------------------
            tranche_idx = tranche_store.get_tranche_index(header_hash=header_hash)

            tranche = Tranche(
                tranche_index=tranche_idx,
                header_hash=header_hash
            )

            # ----------------------- break received judgment -----------------
            epoch_index = data.judgment.epoch_index
            validator_index = data.judgment.validator_index
            validity = data.judgment.validity
            wr_hash = data.judgment.work_report_hash
            edd2519_signature = data.judgment.ed25519_signature

            # as soon as we false judgment we discard after tranche all block process build a new chain
            if not validity:
                # 1. find report => block header, from which block he exist
                wr_header = self.find_report_header(block=latest_block, wr_hash=wr_hash)
                # 2 save state hash
                state.revert(wr_header.hash())  # asking for cache
                # 3. save extrinsic


                # 3. terminate all node further process and process further block


                # stop further process start new chain here

            tranche_store.update_judgment(
                tranche=tranche,
                validator_index=validator_index,
                judgment=validity,
                wr_hash=wr_hash,
                edd2519_signature=edd2519_signature,
                ed25519_public=settings.ed25519_public
            )

            logger.debug(
                "Received Judgment from auditor",
                stream_id=stream_id,
                peer=server,
                buffer_size=len(buffer[1:]),
            )

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            ack = b""
            server.stream_and_close(ack, stream_id)

        except Exception as e:
            # Stop Streaming
            server.stop_stream(stream_id, 1)
            logger.error(
                "Error while intercepting Judgement",
                auditor=server,
                stream_id=stream_id,
                error=str(e),
                err_type=type(e).__name__,
            )

    def res_intercept(self, stream_id: int, client: NodeConnection):
        """Intercept judgment Acknowledgement"""
        buffer = client.stream_buffer[stream_id]

        if buffer == b"":
            logger.info(
                "Judgment acknowledge received",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )
            return True

        return False

    @staticmethod
    def find_report_header(block: Block, wr_hash: WorkReportHash) -> Header:
        """ """
        from jam.state.state import state, State
        from jam.settings import settings

        kv = settings.main_db

        parent_hash = block.header.parent

        curr_available_wrs = state.rho
        found = False
        for r in curr_available_wrs:
            if r.hash() == wr_hash:
                found = True
                break

        if found:
            return block.header

        else:
            while True:
                curr_block = block
                parent_block = curr_block.load_parent(kv)
                # check only upto unaudited block, stop iteration if we find audited, finalized block
                if block.extrinsic.disputes != empty():
                    guarantee_ext = parent_block.extrinsic.guarantees
                    for report, slot, signature in guarantee_ext:
                        if report.hash() == wr_hash:
                            return parent_block.header
                    # if not found we come here
                    block = parent_block

                else:
                    # if dispute not in block, skip that block iterations
                    block = parent_block.load_parent(kv)