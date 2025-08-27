import asyncio
from typing import cast, Tuple

from tsrkit_types import Uint, structure, TypedVector, Bytes, U8

from jam.logging import get_logger

from jam.network.connection import NodeConnection
from jam.network.protocols.ce_137 import CE137Data
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.types.work.manifest import Justification, Assurers
from jam.types.work.shard import BundleShard, SegmentsShard

from jam.network.base.protocol import NetworkProtocol, PrefixType

from jam.storage.da.audits import AuditShardsDA, JustificationsDA
from jam.storage.da.segments import SegmentShardsDA

from jam.utils.merkle import BMRFunctions
from jam.utils.gather import gather_with_exceptions

# Module-specific logger
logger = get_logger("network")

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

    async def transmit(self, data: CE138Data, assurers: Assurers = None):
        """Transmit Erasure-Root and Shard Index from Auditor to Assurer"""

        from jam.network.start import node
        query = data.query
        msg_a = data.query.encode()
        len_a = data.len.encode()

        logger.info(
            f"Transmitting shard index & erasure root to {len(assurers)} assurer"
        )

        tasks = TypedVector([])
        try:
            for client in node.all_connected:
                if client.validator_index not in assurers:
                    continue

                logger.debug(
                    "Requesting audit shard",
                    peer=client,
                    er_root=query.erasure_root.hex(),
                    s_ind=query.shard_index,
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

            return await gather_with_exceptions(tasks)

        except Exception as e:
            logger.error(
                "Failed to request audit shard.",
                er_root=query.erasure_root.hex(),
                s_ind=query.shard_index,
                error=str(e),
                error_type=type(e).__name__,
            )

    def req_intercept(self, stream_id: int, server: NodeConnection):
        """Intercept & Process Erasure-Root and Shard Index on Assurer"""
        from jam.settings import settings

        buffer = server.stream_buffer[stream_id][1:]

        logger.info("Received Shard index & erasure root")

        try:
            data = CE138Data.decode(buffer)
            data = cast(CE138Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            erasure_root = data.query.erasure_root
            shard_index = data.query.shard_index

            d3l = settings.d3l
            audit = settings.audit_da

            # Fetch Segments Shard
            ss_da = SegmentShardsDA(d3l)
            ss_dict = ss_da.get(erasure_root)

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
            merklizer = BMRFunctions()
            segment_shard = SegmentsShard(ss_dict[shard_index].shard)
            segments_shard_root = merklizer.wb_merklize(values=segment_shard)
            s = Bytes(segments_shard_root.encode())

            justification.append(s)

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
            # Stop Streaming
            server.stop_stream(stream_id, 1)

            logger.error(
                "Failed to find audit shard.", error=str(e), error_type=type(e).__name__
            )

    def res_intercept(
            self, stream_id: int, client: NodeConnection
    ) -> Tuple[BundleShard, Justification] | None:
        """Intercept Bundle Shard and Justification"""
        buffer = client.stream_buffer[stream_id]

        try:
            data = CE138Response.decode(buffer)
            data = cast(CE138Response, data)

            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            logger.info("Audit Shard received", peer=client)

            return data.bundle_shard, data.justification

        except Exception as e:
            logger.error(Code.BAD_RESPONSE, error=str(e))
            return None
