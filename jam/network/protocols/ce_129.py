from typing import cast, TYPE_CHECKING

from tsrkit_types import Bytes, TypedVector, Dictionary

from jam.logging import get_logger
from jam.network.base.quic import QuicProtocol
from jam.state.state import state
from jam.types import HeaderHash

if TYPE_CHECKING:
    from jam.network.node import Node

from tsrkit_types.integers import U32
from tsrkit_types.struct import structure
from jam.network.base.protocol import NetworkProtocol, PrefixType

# Module-specific logger
logger = get_logger("network")


@structure
class CE129Data:
    header: HeaderHash
    start: Bytes[31]
    end: Bytes[31]
    max_size: U32


class StateRequest(NetworkProtocol):
    """
    CE 129 Protocol for handling State requests

    Protocol Flow:
            Node -> Node

            --> Header Hash ++ Key (Start) ++ Key (End) ++ Maximum Size
            --> FIN
            <-- [Boundary Node]
            <-- [Key ++ Value]
            <-- FIN
    Source:
            https://github.com/zdave-parity/jam-np/blob/main/simple.md#ce-129-state-request
    """

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE129

    async def transmit(self, node: "Node", data: CE129Data):
        """Transmit State Request"""

        stream_data = data.encode()

        logger.info(
            "Transmitting state request to node",
            header_hash=data.header,
            start=data.start,
            end=data.end,
            max_len=data.max_size,
        )

        transmitted_count = 0
        responses = []
        for peer in node.peer_conn:
            _, client = node.peer_conn[peer]

            try:
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())
                data = await client.close_and_wait(
                    message=stream_data, stream_id=stream_id
                )
                transmitted_count += 1
                responses.append(data)

                logger.debug(
                    "State request transmitted to node", peer=peer, stream_id=stream_id
                )
            except Exception as e:
                responses.append(None)
                logger.error(
                    "Failed to transmit state request",
                    peer=peer,
                    error=str(e),
                    error_type=type(e).__name__,
                )

        logger.info(
            "State request transmission completed",
            transmitted_to=transmitted_count,
        )

        return responses

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept & Process Work Package on Guarantor (server)"""
        from jam.settings import settings

        node = server.node
        buffer = server.stream_buffer[stream_id]

        try:
            logger.debug(
                "Received state request",
                peer=server.peer,
                stream_id=stream_id,
                buffer_size=len(buffer),
            )

            data, offset = CE129Data.decode_from(buffer)
            data = cast(CE129Data, data)

            logger.info(
                "Processing state request",
                stream_id=stream_id,
                header_hash=data.header,
                start=data.start,
                end=data.end,
                max_len=data.max_size,
            )

            # TODO: we are ignoring the header hash, to be updated upon #194 [state variants]

            # Boundaries
            boundaries = set(state.TRIE.get_boundaries(data.start[0:31]))
            end_boundaries = state.TRIE.get_boundaries(data.end[0:31])
            # Join them, remove duplicates
            boundaries.update(end_boundaries)

            boundaries_data = TypedVector[Bytes[64]](list(boundaries)).encode()
            server.stream_and_keep_open(stream_id=stream_id, message=boundaries_data)

            logger.debug(
                "Start and End boundaries shared successfully",
                peer=server.peer,
                stream_id=stream_id,
                len=len(boundaries_data),
            )

            # Key Vals
            _state_data_raw: dict = settings.state_db.get_range(data.start, data.end)
            state_data = Dictionary[Bytes[32], Bytes]({})
            for k, v in _state_data_raw:
                state_data[Bytes[32](k)] = Bytes(v)

            # Return all key val pairs
            key_val_data = state_data.encode()
            server.stream_and_close(stream_id, key_val_data)

            logger.info(
                "State response complete. Closed stream",
                stream_id=stream_id,
                peer=server.peer,
                size=len(key_val_data),
            )

        except Exception as e:
            logger.error(
                "Error processing state request",
                stream_id=stream_id,
                peer=server.peer,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__,
            )

    def res_intercept(self, stream_id: int, client: QuicProtocol):
        """Intercept Acknowledgement"""
        buffer = client.stream_buffer[stream_id]

        logger.info(
            "State request ack received",
            stream_id=stream_id,
            peer=client.peer,
            buffer_size=len(buffer),
        )
