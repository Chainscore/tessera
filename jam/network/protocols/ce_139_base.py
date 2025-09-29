import asyncio
from typing import cast

from tsrkit_types import structure, TypedVector, Uint, U8

from jam.log_setup import logger
from jam.network.connection import NodeConnection
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.types.work.manifest import (
    SegmentIndex,
    Justification,
    Justifications,
    Assurers,
)
from jam.types.work.shard import ShardIndex, SegmentsShard

from jam.network.base.protocol import NetworkProtocol, PrefixType

from jam.types.protocol.core import ErasureRoot, ValidatorIndex
from jam.utils.gather import gather_with_exceptions


SegmentIndexes = TypedVector[SegmentIndex]


@structure
class Query:
    erasure_root: ErasureRoot
    shard_index: ShardIndex
    seg_indexes: SegmentIndexes


class Queries(TypedVector[Query]):
    def hex_roots(self):
        roots = []
        for query in self:
            roots.append(query.erasure_root.hex()[:8] + "...")

        return roots


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

    def __init__(self, prefix: PrefixType):
        super().__init__()
        self._prefix = prefix

    async def transmit(self, data: CE139Data, peers: Assurers = None):
        """Transmit Erasure-Root and Shard Index from Guarantor to Assurer"""
        from jam.network.start import node

        msg_a = data.queries.encode()
        len_a = data.len.encode()

        logger.info(f"Sending segment shard request with")

        tasks = []
        try:
            for client in node.all_connected:
                if client and client.validator_index not in peers:
                    continue

                logger.debug(
                    "Requesting segment shard",
                    peer=client,
                    queries=len(data.queries),
                    roots=data.queries.hex_roots(),
                )

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # set prefix and buffer
                client.stream_prefix[stream_id] = U8(self._prefix)
                client.stream_buffer[stream_id] = b""

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                res = client.close_and_wait(message=msg_a, stream_id=stream_id)

                task = asyncio.create_task(res)
                tasks.append(task)

            responses = await gather_with_exceptions(tasks)
            if responses is not None:
                return responses

        except Exception as e:
            logger.error(
                "Failed to request shards", error=str(e), error_type=type(e).__name__
            )

    @staticmethod
    def parse_request(buffer: bytes) -> CE139Data:
        data = CE139Data.decode(buffer)
        data = cast(CE139Data, data)

        if not data.is_valid:
            raise NetworkingError(Code.INVALID_DATA)

        return data

    def req_intercept(self, stream_id: int, server: NodeConnection):
        ...

    def res_intercept(self, stream_id: int, client: NodeConnection):
        ...
