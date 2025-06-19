from typing import Any

from anyio.to_process import process_worker
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.network.quic import QuicServerProtocol
from jam.types.base.sequences.vector import Vector
from jam.types.base.integers import Int
from jam.types.base.boolean import Boolean

from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from dataclasses import dataclass
from jam.utils.json import JsonSerde
from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature, Hash
from jam.config.logging import logger
from jam.types.base.null import Null
from typing import cast




@decodable_dataclass
@dataclass
class CE145Data(Codable, JsonSerde):
    epoch_index: Int
    validator_index: Int
    validity: Boolean
    work_report_hash: WorkReportHash
    ed25519_signature: Ed25519Signature


class JudgmentPublication(NetworkProtocol):
    """
    CE 144 Protocol (Judgment Publication ) => Announcement of judgement.

    Protocol Flow:
        Auditor -> Validator

        --> Epoch Index ++ Validator Index  ++ Validity ++ Work-report Hash ++ Ed25529 Signature
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
        """ Announcement of a judgment for the particular work report"""
        logger.info(f"Transmitting Work-report judgement")

        message = self._prefix.encode() + data.encode()

        responses = Vector([])
        for peer in node.peer_conn:
            if int(peer.data.metadata.port) == 30336:
                logger.info("sending report to 30336")
                client = node.peer_conn[peer][1]
                data = await client.stream_and_close(message=message)

    def server_intercept(self, node: Node, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        data, offset = CE145Data.decode_from(buffer)
        data = cast(CE145Data, data)

        logger.info(f"Receive assurance for the work report")

        # TODO: Save the auditing somewhere
        # process_work_package = pe
        report = data.work_report_hash


    def client_intercept(self, node: Node, buffer: bytes, stream_id: int):
        return Null