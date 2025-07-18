from typing import cast, Tuple

from tsrkit_types import Uint, structure, TypedVector

from jam.logging import logger

from jam.network.base.jamnp import JAMNP
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

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE138

    async def transmit(self, data: CE138Data):
        """Transmit Erasure-Root and Shard Index from Auditor (client) to Assurer (server)"""
        
        from jam.network.node import node 

        msg_a = data.query.encode()
        len_a = data.len.encode()

        logger.info(f"Transmitting shard index & erasure root to {len(node._protocols)} assurer")

        responses = TypedVector([])
        for client in node._protocols.values():
            if int(client.val.metadata.port) == 30336:
                logger.info("requesting audit shard from 30336")

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                data = await client.close_and_wait(message=msg_a, stream_id=stream_id)

                responses.append(data)

        return responses

    def req_intercept(self, stream_id: int, server: JAMNP):
        """Intercept & Process Erasure-Root and Shard Index on Assurer (server)"""
        from jam.settings import settings

        buffer = server.stream_buffer[stream_id]

        logger.info("Received Shard index & erasure root")
        data = CE138Data.decode(buffer[1:])

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
        self, stream_id: int, client: JAMNP
    ) -> Tuple[BundleShard, Justification] | None:
        """Intercept Bundle Shard and Justification"""
        buffer = client.stream_buffer[stream_id]

        try:
            data = CE138Response.decode(buffer[1:])

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
