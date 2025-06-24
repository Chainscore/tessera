from typing import cast, Tuple

from tsrkit_types import structure, Uint, Null

from jam.config.logging import logger
from jam.config.settings import settings

from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.quic import QuicProtocol

from jam.types.protocol.core import ErasureRoot
from jam.types.work.manifest import Justification
from jam.types.work.shard import BundleShard, SegmentsShard, ShardIndex

from jam.work_package.stores.audits import AuditShardsDA, JustificationsDA
from jam.work_package.stores.segments import SegmentShardsDA

@structure
class Query:
    erasure_root: ErasureRoot
    shard_index: ShardIndex

@structure
class CE137Data:
    len: Uint[32]
    query: Query

    @property
    def is_valid(self):
        if len(self.query.encode()) == self.len:
            return True
        return False

@structure
class CE137Response:
    bs_len: Uint[32]
    bundle_shard: BundleShard
    ss_len: Uint[32]
    segments_shard: SegmentsShard
    j_len: Uint[32]
    justification: Justification

    @property
    def is_valid(self):
        if (len(self.bundle_shard.encode()) == self.bs_len
                and len(self.segments_shard.encode()) == self.ss_len
                and len(self.justification.encode()) == self.j_len):
            return True
        return False


class ShardDistributionProtocol(NetworkProtocol):
    """
        CE 137 Protocol for shard distribution

        Assurer -> Guarantor

        --> Erasure-Root ++ Shard Index
        --> FIN
        <-- Bundle Shard
        <-- [Segment Shard] (Should include all exported and proof segment shards with the given index)
        <-- Justification
        <-- FIN

        Source:
            https://docs.jamcha.in/advanced/simple-networking/spec#ce-137-shard-distribution
    """

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE137

    async def transmit(self, node: Node, data: CE137Data):
        """Transmit Erasure-Root and Shard Index from Assurer (client) to Guarantor (server)"""

        msg_a = data.query.encode()
        len_a = data.len.encode()

        logger.info(f"Requesting shard from {len(node.peer_conn)} guarantors")

        for peer in node.peer_conn:
            try:
                if int(peer.port) == 40002:
                    logger.debug("Requesting shard from", peer=str(peer))
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

            except Exception as e:
                logger.error(
                    "Failed to request shard.",
                    peer=str(peer),
                    error=str(e),
                    error_type=type(e).__name__
                )

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept & Process Erasure-Root and Shard Index on Guarantor (server)"""
        buffer = server.stream_buffer[stream_id]

        try:
            data, offset = CE137Data.decode_from(buffer[1:])
            data = cast(CE137Data, data)

            logger.info(
                "Received shard request",
                erasure_root=data.query.erasure_root,
                shard_index=data.query.shard_index,
                peer=server.peer
            )

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            # TODO: Process received erasure root & shard index
            query = data.query

            d3l = settings.d3l
            audit = settings.audit

            justification_da = JustificationsDA(audit)

            # Fetch Bundle Shard
            audits_da = AuditShardsDA(audit)
            bs_dict = audits_da.get(query.erasure_root)
            bundle_shard = BundleShard(bs_dict[query.shard_index])

            # Fetch Segments Shard
            ss_da = SegmentShardsDA(d3l)
            ss_dict = ss_da.get(query.erasure_root)
            if query.shard_index not in ss_dict:
                raise "Shard not found"

            segments_shard = SegmentsShard(ss_dict[query.shard_index].shard)

            # TODO: Fetch Justifications
            justification = Justification([])

            # Return requested shards
            msg_a = bundle_shard.encode()
            len_a = Uint[32](len(msg_a)).encode()
            msg_b = segments_shard.encode()
            len_b = Uint[32](len(msg_b)).encode()
            msg_c = justification.encode()
            len_c = Uint[32](len(msg_c)).encode()

            server.stream_and_keep_open(len_a, stream_id)
            server.stream_and_keep_open(msg_a, stream_id)
            server.stream_and_keep_open(len_b, stream_id)
            server.stream_and_keep_open(msg_b, stream_id)
            server.stream_and_keep_open(len_c, stream_id)
            server.stream_and_close(msg_c, stream_id)

        except Exception as e:
            msg_a = Null.encode()
            len_a = Uint[32](len(msg_a)).encode()

            # Send response
            server.stream_and_keep_open(len_a, stream_id)
            server.stream_and_close(msg_a, stream_id)

            logger.error(
                "Error processing shard request",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__
            )

    def res_intercept(self, stream_id: int, client: QuicProtocol) -> Tuple[BundleShard, SegmentsShard, Justification] | None:
        """Intercept Bundle Shard, [Segment Shard] and Justification"""
        buffer = client.stream_buffer[stream_id]

        try:
            data, offset = CE137Response.decode_from(buffer[1:])
            data = cast(CE137Response, data)

            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            logger.info("Data received on Assurer Node")

            # TODO: verify justification
            # TODO: save the justification for CE139/140 and proceed further with data

            return data.bundle_shard, data.segments_shard, data.justification

        except Exception as e:
            logger.error(Code.BAD_RESPONSE, error=str(e))
            return None
