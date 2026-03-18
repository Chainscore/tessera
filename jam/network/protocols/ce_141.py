import asyncio
from tsrkit_types import structure, U32, U8
from typing import cast

from jam.network.connection import PeerConnection
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.types import ValidatorIndex
from jam.block.extrinsics.assurances import AvailAssurance, AvailBitField
from jam.types.protocol.crypto import Ed25519Signature, HeaderHash
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.utils.gather import gather_with_exceptions

@structure
class Assurance:
    anchor_hash: HeaderHash
    bitfield: AvailBitField
    ed25519_signature: Ed25519Signature


@structure
class CE141Data:
    len: U32
    assurance: Assurance

    @property
    def is_valid(self):
        if len(self.assurance.encode()) == self.len:
            return True
        return False


class AssuranceDistribution(NetworkProtocol):
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

    _prefix = PrefixType.CE141

    async def transmit(self, data: CE141Data):
        """Transmit assurance, From Assurer (client) to Validator (server)"""
        node = self.jam.router.node

        msg = data.assurance.encode()
        len_a = data.len.encode()

        self.logger.info(
            f"Transmitting assurance of HH {data.assurance.anchor_hash.hex()} to {len(node.all_connected)}  validators"
        )

        try:
            tasks = []

            for client in node.all_connected:
                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # set prefix and buffer
                client.stream_prefix[stream_id] = U8(self._prefix)
                client.stream_buffer[stream_id] = b""

                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                res = client.close_and_wait(message=msg, stream_id=stream_id)
                task = asyncio.create_task(res)
                tasks.append(task)

            responses = await gather_with_exceptions(tasks)

            return responses

        except Exception as e:
            self.logger.error(
                "Failed to transmit assurance",
                hash=data.assurance.anchor_hash.hex()[16:]+"...",
                error=str(e),
                error_type=type(e).__name__,
            )

    async def req_intercept(self, stream_id: int, server: PeerConnection):

        try:
            buffer = server.stream_buffer[stream_id][1:]

            data = CE141Data.decode(buffer)
            data = cast(CE141Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            assurance = data.assurance
            vi = ValidatorIndex(server.validator_index)

            assurance_extrinsic = AvailAssurance(
                anchor=assurance.anchor_hash,
                bitfield=assurance.bitfield,
                validator_index=vi,
                signature=assurance.ed25519_signature,
            )

            self.logger.debug(
                "Received assurance",
                peer=server,
                assurance=assurance_extrinsic.to_json(),
            )

            # Store Assurance Extrinsic
            self.pool.assurances.store(assurance_extrinsic)

            # Return acknowledgment to Builder
            ack = b""
            server.stream_and_close(ack, stream_id)
            self.logger.debug(
                "Assurance Acknowledgement sent back to validator",
                validator=server, stream_id=stream_id, ack_size=len(ack)
            )

        except Exception as e:
            # Stop Streaming
            server.stop_stream(stream_id, 1)

            self.logger.error(
                "Failed to process assurances",
                error=str(e),
                error_type=type(e).__name__,
            )

    async def res_intercept(self, stream_id: int, client: PeerConnection):
        buffer = client.stream_buffer[stream_id]
        if buffer == b"":
            self.logger.debug(
                "Assurance acknowledgement received",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )
            return True

        return False
