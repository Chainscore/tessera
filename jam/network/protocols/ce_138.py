from typing import cast, Tuple

from tsrkit_types import Uint, structure, TypedVector

from jam.logging import logger

from jam.network.base.quic import QuicProtocol
from jam.network.protocols.ce_137 import CE137Data
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.types.work.manifest import Justification
from jam.types.work.shard import BundleShard

from jam.network.base.protocol import NetworkProtocol, PrefixType

from jam.storage.da.audits import AuditShardsDA, JustificationsDA
from jam.storage.da.segments import SegmentShardsDA


CE138Data = CE137Data


@structure
class CE138Response:
    bs_len: Uint[32]
    bundle_shard: BundleShard
    j_len: Uint[32]
    justification: Justification

    @property
    def is_valid(self):
        if (
            len(self.bundle_shard.encode()) == self.bs_len
            and len(self.justification.encode()) == self.j_len
        ):
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

        responses = TypedVector([])
        for peer in node.peer_conn:
            if int(peer.port) == 30336:
                logger.info("requesting audit shard from 30336")
                client = node.peer_conn[peer][1]

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                data = await client.close_and_wait(message=msg_a, stream_id=stream_id)

                responses.append(data)

        return responses

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept & Process Erasure-Root and Shard Index on Assurer (server)"""
        from jam.settings import settings

        buffer = server.stream_buffer[stream_id]

        logger.info("Received Shard index & erasure root")
        data, offset = CE138Data.decode_from(buffer[1:])
        data = cast(CE138Data, data)

        if not data.is_valid:
            raise NetworkingError(Code.INVALID_DATA)

        query = data.query

        logger.info("Processing")
        # TODO: Process received erasure code & shard index

        d3l = settings.d3l
        audit = settings.audit

        audits_da = AuditShardsDA(audit)
        ss_da = SegmentShardsDA(d3l)
        justification_da = JustificationsDA(audit)

        # Fetch Bundle Shard
        audits_da = AuditShardsDA(audit)
        bs_dict = audits_da.get(query.erasure_root)
        bundle_shard = bs_dict[query.shard_index]

        # TODO: Fetch Justifications
        justification = Justification([])

        # Return requested shards
        msg_a = bundle_shard.encode()
        len_a = Uint[32](len(msg_a)).encode()
        msg_b = justification.encode()
        len_b = Uint[32](len(msg_a)).encode()

        server.stream_and_keep_open(len_a, stream_id)
        server.stream_and_keep_open(msg_a, stream_id)
        server.stream_and_keep_open(len_b, stream_id)
        server.stream_and_close(msg_b, stream_id)

    def res_intercept(
        self, stream_id: int, client: QuicProtocol
    ) -> Tuple[BundleShard, Justification] | None:
        """Intercept Bundle Shard and Justification"""
        buffer = client.stream_buffer[stream_id]

        try:
            data, offset = CE138Response.decode_from(buffer[1:])
            data = cast(CE138Response, data)

            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            logger.info("Data received on Auditor Node")

            # TODO: verify justification
            # TODO: save the justification for CE139/140 and proceed further with data

            logger.info("Received bundle shard")
            return data.bundle_shard, data.justification

        except Exception as e:
            logger.error(Code.BAD_RESPONSE)
            return None
