from typing import Any
from tsrkit_types import structure, Null, bool, U16, Uint
from jam.types.protocol.core import ValidatorIndex

from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.quic import QuicProtocol


from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature, Hash



@structure
class CE145Data:
    epoch_index: Uint[32]                     # mention in networking =>  Epoch Index = u32 (Slot / E)
    validator_index: ValidatorIndex
    validity: bool
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

    async def transmit(self, node: "Node", data: Any):
        """ Announcement of a judgment for the particular work report"""
        logger.info(f"Transmitting Work-report judgement")

        message = self._prefix.encode() + data.encode()

        responses = Vector([])
        for peer in node.peer_conn:
            if int(peer.data.metadata.port) == 30336:
                logger.info("sending report to 30336")
                client = node.peer_conn[peer][1]
                data = await client.stream_and_close(message=message)


        ...

    # def server_intercept(self, node: Node, buffer: bytes, server: QuicServerProtocon, stream_id: int)
    def req_intercept(self, stream_id: int, server: "QuicProtocol"):

        # data, offset = CE145Data.decode_from(buffer)
        # data = cast(CE145Data, data)
        #
        # logger.info(f"Receive assurance for the work report")
        #
        # # TODO: Save the auditing somewhere
        # # process_work_package = pe
        # report = data.work_report_hash
        ...


    def res_intercept(self, stream_id: int, client: "QuicProtocol"):
        return Null