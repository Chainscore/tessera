from typing import cast, TYPE_CHECKING

from tsrkit_types import Bytes, TypedVector, Dictionary

from jam.types import HeaderHash

if TYPE_CHECKING:
    from jam.network.connection import PeerConnection

from tsrkit_types.integers import U32
from tsrkit_types.struct import structure
from jam.network.base.protocol import NetworkProtocol, PrefixType

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

    _prefix = PrefixType.CE129


    async def transmit(self, data: CE129Data):
        """Transmit State Request"""
        node = self.jam.router.node

        stream_data = data.encode()

        self.logger.trace(
            "Transmitting state request to node",
            header_hash=data.header,
            start=data.start,
            end=data.end,
            max_len=data.max_size,
        )

        transmitted_count = 0
        responses = []
        for client in node.all_connected:
            try:
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())
                data = await client.close_and_wait(
                    message=stream_data, stream_id=stream_id
                )
                transmitted_count += 1
                responses.append(data)

                self.logger.debug(
                    "State request transmitted to node",
                    peer=client.peer_id,
                    stream_id=stream_id
                )
            except Exception as e:
                responses.append(None)
                self.logger.error(
                    "Failed to transmit state request",
                    peer=client.peer_id,
                    error=str(e),
                    error_type=type(e).__name__,
                )

        self.logger.info(
            "State request transmission completed",
            transmitted_to=transmitted_count,
        )

        return responses

    async def req_intercept(self, stream_id: int, server: PeerConnection):
        """Intercept & Process Work Package on Guarantor (server)"""
        settings = server.jam.settings
        state = server.jam.state

        buffer = server.stream_buffer[stream_id]

        try:
            self.logger.debug(
                "Received state request",
                peer=server.peer_id,
                stream_id=stream_id,
                buffer_size=len(buffer),
            )

            data, offset = CE129Data.decode_from(buffer)
            data = cast(CE129Data, data)

            self.logger.trace(
                "Processing state request",
                stream_id=stream_id,
                header_hash=data.header,
                start=data.start,
                end=data.end,
                max_len=data.max_size,
            )

            # TODO: we are ignoring the header hash, to be updated upon #194 [state variants]

            # Boundaries
            boundaries = set(state.trie.get_boundaries(data.start[0:31]))
            end_boundaries = state.trie.get_boundaries(data.end[0:31])
            # Join them, remove duplicates
            boundaries.update(end_boundaries)

            boundaries_data = TypedVector[Bytes[64]](list(boundaries)).encode()
            server.stream_and_keep_open(stream_id=stream_id, message=boundaries_data)

            self.logger.trace(
                "Start and End boundaries shared successfully",
                peer=server.peer_id,
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

            self.logger.info(
                "Returned state data to requester.",
                stream_id=stream_id,
                peer=server.peer_id,
                size=len(key_val_data),
            )

        except Exception as e:
            self.logger.error(
                "Error processing state request",
                stream_id=stream_id,
                peer=server.peer_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__,
            )

    async def res_intercept(self, stream_id: int, client: PeerConnection):
        """Intercept Acknowledgement"""
        buffer = client.stream_buffer[stream_id]

        # TODO: Decode state from keyvals, store in DB. Whichever required.

        self.logger.debug(
            "Received requested state key vals.",
            stream_id=stream_id,
            peer=client.peer_id,
            buffer_size=len(buffer),
        )
