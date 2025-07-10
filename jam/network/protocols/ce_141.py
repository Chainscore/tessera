import asyncio

from jam.operations.ext_store import ext_store
from tsrkit_types import structure, TypedVector, U8, Uint, U32
from jam.logging import get_logger
from typing import cast

from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.settings import settings
from jam.types.block.extrinsics.assurances import AvailAssurance, AvailBitField
from jam.types.protocol.crypto import Ed25519Signature, HeaderHash
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code


logger = get_logger("network")

@structure
class Assurance:
    header_hash: HeaderHash
    bitfield: AvailBitField
    ed25519_signature: Ed25519Signature

@structure
class CE141Data:
    assurance: Assurance
    len: U32

    @property
    def is_valid(self):
        if len(self.assurance.encode()) == self.len:
            return True
        return False


class AssuranceDistribution(NetworkProtocol):
    from jam.network.node import Node
    """
    CE-141 Assurance(Validators issue a signed statement, called an assurance) Distribution protocol enables each validator to broadcast an availability assurance for a work report.

    Protocol Flow:
        Assurer -> validator

        --> Assurance
        --> FIN
        <-- FIN
        
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-141-assurance-distribution

    """

    # TODO: Reimplement 141 properly
    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE141

    async def transmit(self, node: Node, data: CE141Data):
        """ Transmit assurance, From Assurer (client) to Validator (server) """

        msg = data.assurance.encode()
        len_a = data.len.encode()

        logger.info(f"Transmitting assurance of HH {data.assurance.header_hash.hex()} to {len(node.peer_conn)}  validators")

        responses = TypedVector([])

        for peer in node.peer_conn:

            client = node.peer_conn[peer][1]

            # Send Protocol Prefix
            stream_id = client.stream_and_keep_open(message=self._prefix.encode())

            # Append prefix to stream buffer so that we know the stream for handling respons
            client.stream_buffer[stream_id] = self._prefix.encode()

            client.stream_and_keep_open(message=len_a, stream_id=stream_id)
            res = await client.close_and_wait(message=msg, stream_id=stream_id)

            responses.append(res)

        return responses


    def req_intercept(self, stream_id: int, server: QuicProtocol):


        buffer = server.stream_buffer[stream_id]

        logger.debug(
            "Received assurance",
            stream_id=stream_id,
            buffer_size=len(buffer[1:])

        )

        data, offset = CE141Data.decode_from(buffer[1:])
        data = cast(CE141Data, data)

        if not data.is_valid:
            raise NetworkingError(Code.INVALID_DATA)

        assurance = data.assurance
        vi = server.peer.peer_index

        assurance_extrinsic = AvailAssurance(
            anchor = assurance.header_hash,
            bitfield = assurance.bitfield,
            validator_index = vi,
            signature= assurance.ed25519_signature
        )

        ext_store.import_assr(assurance_extrinsic)

        # Return acknowledgment to Builder
        ack = b""
        server.stream_and_close(ack, stream_id)

        logger.debug(
            "Assurance sent to other validators",
            stream_id=stream_id,
            ack_size=len(ack)
        )

        asyncio.create_task(self.audit_announcement())

    def res_intercept(self, stream_id: int, client: QuicProtocol):
        buffer = client.stream_buffer[stream_id]
        if buffer[1:] == b"":
            logger.info(
                "Assurance ack received",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )
            return True

        return False



