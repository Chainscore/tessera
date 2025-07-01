from typing import cast

from tsrkit_types import structure, TypedVector, Uint

from jam.config.logging import logger
from jam.network.base.quic import QuicProtocol
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.types.work.manifest import SegmentIndex, Justification, Justifications
from jam.types.work.shard import ShardIndex, SegmentsShard

from jam.network.base.protocol import NetworkProtocol, PrefixType

from jam.types.protocol.core import ErasureRoot, ValidatorIndex


SegmentIndexes = TypedVector[SegmentIndex]

@structure
class Query:
    erasure_root : ErasureRoot
    shard_index: ShardIndex
    seg_indexes : SegmentIndexes

Queries = TypedVector[Query]

@structure
class CE139Data:
    len: Uint[32]
    queries: Queries

    @property
    def is_valid(self):
        if len(self.queries.encode()) == self.len:
            return True
        return False

@structure()
class CE139Response:
    len: Uint[32]
    s_shards: SegmentsShard

    @property
    def is_valid(self):
        if len(self.s_shards.encode()) == self.len:
            return True
        return False

@structure
class CE140Justification:
    len: Uint[32]
    justification: Justification

    @property
    def is_valid(self):
        if len(self.justification.encode()) == self.len:
            return True
        return False

CE140Data = CE139Data


class SegmentShardRequestBase(NetworkProtocol):

    from jam.network.node import Node

    def __init__(self, prefix: PrefixType):
        super().__init__()
        self._prefix = prefix

    async def transmit(self, node: Node, data: CE139Data):
        """Transmit Erasure-Root and Shard Index from Guarantor to Assurer"""

        msg_a = data.queries.encode()
        len_a = data.len.encode()

        logger.info(f"Sending segment shard request with")

        for peer in node.peer_conn:
            if int(peer.port) == 40000:
                logger.info("requesting seg shard from 40000")
                client = node.peer_conn[peer][1]

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                res = await client.close_and_wait(message=msg_a, stream_id=stream_id)

                if res is not None:
                    return res

    @staticmethod
    def parse_request(buffer: bytes) -> CE139Data:
        data, _ = CE139Data.decode_from(buffer)
        data = cast(CE139Data, data)

        if not data.is_valid:
            raise NetworkingError(Code.INVALID_DATA)

        return data

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        ...

    def res_intercept(self, stream_id: int, client: QuicProtocol):
        ...

