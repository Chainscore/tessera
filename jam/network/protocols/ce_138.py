import asyncio
from typing import cast, Tuple

from tsrkit_types import Uint, structure, TypedVector, Bytes, Null

from jam.logging import logger

from jam.network.base.quic import QuicProtocol
from jam.network.protocols.ce_137 import CE137Data
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.types.work.manifest import Segment, Justification
from jam.types.work.shard import SegmentsShard, ShardIndex, BundleShard, ShardKey

from jam.network.base.protocol import NetworkProtocol, PrefixType

from jam.work_package.stores.audits import AuditShardsDA, JustificationsDA
from jam.work_package.stores.segments import SegmentShardsDA
from jam.merklization import BMRFunctions
from jam.types.protocol.crypto import Hash
from jam.utils.gather import gather_with_exceptions


class CE138Data(CE137Data):
    ...

@structure
class CE138Response:
    bs_len: Uint[32]
    bundle_shard: BundleShard
    j_len: Uint[32]
    justification: Justification

    @property
    def is_valid(self):
        if (len(self.bundle_shard.encode()) == self.bs_len
                and len(self.justification.encode()) == self.j_len):
            return True
        return False

class AuditShardRequestProtocol(NetworkProtocol):
    """
        CE 138 Protocol for Audit shard request

        Auditor -> Assurer

        --> Erasure-Root ++ Shard Index
        --> FIN
        <-- Bundle Shard
        <-- Justification
        <-- FIN

        Source:
            https://docs.jamcha.in/advanced/simple-networking/spec#ce-138-shard-distribution
    """

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE138

    async def transmit(self, node: Node, data: CE138Data):
        """Transmit Erasure-Root and Shard Index from Auditor (client) to Assurer (server)"""

        msg_a = data.query.encode()
        len_a = data.len.encode()

        logger.info(f"Transmitting shard index & erasure root to {len(node.peer_conn)} assurer")

        tasks = TypedVector([])
        try:
            for peer in node.peer_conn:
                logger.info("Requesting audit shard from peer", port=peer.port)
                client = node.peer_conn[peer][1]

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

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
                "Failed to request audit shard.",
                error=str(e),
                error_type=type(e).__name__
            )


    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept & Process Erasure-Root and Shard Index on Assurer (server)"""
        from jam.settings import settings
        buffer = server.stream_buffer[stream_id]

        logger.info("Received Shard index & erasure root")
        data, offset = CE138Data.decode_from(buffer[1:])
        data = cast(CE138Data, data)

        print("Recieved data", data)

        try:
            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            erasure_root = data.query.erasure_root
            shard_index = data.query.shard_index

            d3l = settings.d3l
            audit = settings.audit_da

            # Fetch Segments Shard
            ss_da = SegmentShardsDA(d3l)
            ss_dict = ss_da.get(erasure_root)

            print("segment shard", ss_dict[shard_index])

            # Fetch Bundle Shard
            audits_da = AuditShardsDA(audit)
            bs_dict = audits_da.get(erasure_root)
            if shard_index not in bs_dict.keys():
                raise ValueError("Bundle shard not found")
            bundle_shard = bs_dict[shard_index]

            # Fetch Justifications
            justification_da = JustificationsDA(audit)
            justification = justification_da.get(erasure_root, shard_index)

            # build segment shard root
            bmrfunctions = BMRFunctions()
            segment_shard = SegmentsShard(ss_dict[shard_index].shard)
            segments_shard_root = bmrfunctions.wb_merkle_fn(values=segment_shard)
            s = Bytes(segments_shard_root.encode())

            justification.append(s)

            print("bundle shard", bundle_shard)

            # Return requested shards
            msg_a = bundle_shard.encode()
            len_a = Uint[32](len(msg_a)).encode()
            msg_b = justification.encode()
            len_b = Uint[32](len(msg_b)).encode()

            server.stream_and_keep_open(len_a, stream_id)
            server.stream_and_keep_open(msg_a, stream_id)
            server.stream_and_keep_open(len_b, stream_id)
            server.stream_and_close(msg_b, stream_id)

        except Exception as e:
            msg_a = Bytes(b'').encode()
            len_a = Uint[32](len(msg_a)).encode()
            msg_b = Bytes(b'').encode()
            len_b = Uint[32](len(msg_a)).encode()

            # Send response
            server.stream_and_keep_open(len_a, stream_id)
            server.stream_and_keep_open(msg_a, stream_id)
            server.stream_and_keep_open(len_b, stream_id)
            server.stream_and_close(msg_b, stream_id)
            logger.error(
                "Failed to find audit shard.",
                error=str(e),
                error_type=type(e).__name__
            )


    def res_intercept(self, stream_id: int, client: QuicProtocol) -> Tuple[BundleShard, Justification] | None:
        """Intercept Bundle Shard and Justification"""
        buffer = client.stream_buffer[stream_id]

        try:
            data, offset = CE138Response.decode_from(buffer[1:])
            data = cast(CE138Response, data)

            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            logger.info("Data received on Auditor Node")

            logger.info("Received bundle shard")
            return data.bundle_shard, data.justification

        except Exception as e:
            logger.error(Code.BAD_RESPONSE, error=e)
            return None