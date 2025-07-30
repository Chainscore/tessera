from typing import cast
from tsrkit_types import structure, Uint, Bool

from jam.types.protocol.core import ValidatorIndex, EpochIndex

from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.quic import QuicProtocol
from jam.logging import get_logger
from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature

from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

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
        Auditor -> Auditor

        --> Epoch_index ++ Validator_Index ++ Validity ++ Work_Report_Hash ++ Ed25519_Signature
        --> FIN
        <-- FIN

    sources:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-145-judgment-publication

    """

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE145

    async def transmit(self, node: Node, data: CE145Data):
        """Transmit Judgments for the particular Work Report to other Auditors"""

        len_a = data.len_a.encode()
        msg_a = data.judgment.encode()

        logger.info(
            f"Transmitting Work-report judgement",
            judgment=data.judgment,
            len_a=data.len_a
        )

        tasks = []
        responses = []
        transmitted_count = 0

        try:
            logger.info(f"Transmitting Judgment to {len(node.peer_conn)} validators")

            for peer in node.peer_conn:
                client = node.peer_conn[peer][1]

                # send protocol prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

                transmitted_count += 1

                # send message with their length
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)

                res = await client.close_and_wait(message=msg_a, stream_id=stream_id)
                responses.append(res)

                logger.debug(
                    "Judgment transmitted",
                    stream_id=stream_id,
                    port=peer.port,
                    validator=peer,
                )

        except Exception as e:
            logger.error(
                "Failed to transmitting Judgment",
                error=str(e),
                error_type=type(e).__name__,
            )

        return responses

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept individual Judgment from other Auditors for their assigned Work Reports """
        from jam.operations.tranche_store import tranche_store, Tranche
        from jam.finality.finality import Finality
        from jam.settings import settings
        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()

        buffer = server.stream_buffer[stream_id]

        try:
            data = CE145Data.decode(buffer[1:])
            data = cast(CE145Data, data)

            # JUDGMENT RECEIVED FROM WHICH VALIDATOR THAT INDEX, JUDGMENT, WR_HASH
            vi_judgment = data.judgment.validator_index
            judge = data.judgment.validity
            wr_hash = data.judgment.work_report_hash

            tranche_idx = tranche_store.get_tranche_index(header_hash=header_hash)

            tranche=Tranche(
                tranche_index=tranche_idx,
                header_hash=header_hash
            )

            tranche_store.update_judgment( tranche=tranche, wr_hash=wr_hash, judgment=judge, validator_index=vi_judgment)

            logger.debug(
                "Received Judgment from other Auditors",
                stream_id=stream_id,
                peer=server.peer,
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
                "Error while intercepting Judgement'",
                auditor=server.peer,
                stream_id=stream_id,
                error=str(e),
                err_type=type(e).__name__,
            )

    def res_intercept(self, stream_id: int, client: "QuicProtocol"):
        """Intercept judgment Acknowledgement"""
        buffer = client.stream_buffer[stream_id]

        if buffer[1:] == b"":
            logger.info(
                "Judgment acknowledge received",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )
            return True

        return False
