from typing import cast, Tuple

from tsrkit_types import Vector, Uint

from jam.network.base.quic import QuicProtocol
from jam.network.protocols.ce_139_base import SegmentShardRequestBase, Justifications, CE139Response, CE140Justification
from jam.network.base.protocol import PrefixType
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.logging import logger
from jam.merklization import BMRFunctions

from jam.types.work.shard import SegmentsShard, SegmentShard

from jam.work_package.stores.segments import SegmentShardsDA


class SegmentShardRequestWithJustifications(SegmentShardRequestBase):
    """
        CE 140 Protocol for Requesting Segments Shards from Assurers

        Protocol Flow:
            Guarantor -> Assurers

            --> [Erasure-Root ++ Shard Index ++ len++[Segment Index]]
            --> FIN
            <-- [Segment Shard]
                for each segment shard {
                    <-- Justification
                }
            <-- FIN
        Source:
            https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-139140-segment-shard-request
    """
    from jam.network.node import Node

    def __init__(self):
        super().__init__(PrefixType.CE140)

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept & Process Erasure-Root, Shard Index & Segment Indices on Assurer"""
        from jam.settings import settings
        buffer = server.stream_buffer[stream_id]

        try:
            request = self.parse_request(buffer[1:])

            d3l = settings.d3l
            ss_da = SegmentShardsDA(d3l)

            # Fetching segments...
            shards = SegmentsShard([])

            # TODO: Fix Justifications
            justifications = Justifications([])
            merkle = BMRFunctions()

            for query in request.queries:
                ss_dict = ss_da.get(query.erasure_root)
                s_dict = ss_dict[query.shard_index]
                for index in query.seg_indexes:
                    shards.append(s_dict[index])


            # Return requested shards & justifications
            msg_a = shards.encode()
            len_a = Uint[32](len(msg_a)).encode()

            server.stream_and_keep_open(len_a, stream_id)
            server.stream_and_keep_open(msg_a, stream_id)

            n = len(justifications)
            for ind, jfn in enumerate(justifications):
                msg_n = jfn.encode()
                len_n = Uint[32](len(msg_n)).encode()
                server.stream_and_keep_open(len_n, stream_id)

                if ind == n-1:
                    server.stream_and_close(msg_n, stream_id)
                else:
                    server.stream_and_keep_open(msg_n, stream_id)
        except Exception as e:
            logger.error(
                "Failed to request shards using ce_140",
                error=str(e),
                error_type=type(e).__name__
            )



    def res_intercept(self, stream_id: int, client: QuicProtocol) -> Tuple[SegmentsShard, Justifications] | None:
        """Intercept [Segment Shard] and Justification"""
        buffer = client.stream_buffer[stream_id]

        try:
            data, offset = CE139Response.decode_from(buffer[1:])
            data = cast(CE139Response, data)

            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            shards = data.s_shards

            k = offset
            justifications = Justifications([])
            while k:
                jfn, i = CE140Justification.decode_from(buffer[1:], k)
                jfn = cast(CE140Justification, jfn)

                if not jfn or not jfn.is_valid:
                    raise NetworkingError(Code.INVALID_DATA)
                justifications.append(jfn.justification)

            logger.info("Received CE140 shard+justification response")

            return shards, justifications

        except Exception as e:
            logger.error(Code.BAD_RESPONSE)
            return None
