from tsrkit_types import Uint
from typing import cast

from jam.network.base.jamnp import JAMNP
from jam.network.protocols.ce_139_base import SegmentShardRequestBase, CE139Response
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.logging import logger

from jam.network.base.protocol import PrefixType
from jam.types.work.shard import SegmentsShard
from jam.storage.da.segments import SegmentShardsDA


class SegmentShardRequest(SegmentShardRequestBase):
    """
    CE 139 Protocol for Requesting Segments Shards from Assurers

    Protocol Flow:
        Guarantor -> Assurers

        --> [Erasure-Root ++ Shard Index ++ len++[Segment Index]]
        --> FIN
        <-- [Segment Shard]
        <-- FIN
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-139140-segment-shard-request
    """

    def __init__(self):
        super().__init__(PrefixType.CE139)

    def req_intercept(self, stream_id: int, server: JAMNP):
        """Intercept & Process Erasure-Root, Shard Index & Segment Indices on Assurer"""
        from jam.settings import settings

        buffer = server.stream_buffer[stream_id]

        request = self.parse_request(buffer[1:])
        logger.info("Handling CE139 shard request")
        d3l = settings.d3l
        ss_da = SegmentShardsDA(d3l)

        # Fetching segments...
        shards = SegmentsShard([])
        for query in request.queries:
            ss_dict = ss_da.get(query.erasure_root)
            s_dict = ss_dict[query.shard_index]
            for index in query.seg_indexes:
                shards.append(s_dict[index])

        # Return requested shards
        msg_a = shards.encode()
        len_a = Uint[32](len(msg_a)).encode()

        server.stream_and_keep_open(len_a, stream_id)
        server.stream_and_close(msg_a, stream_id)

    def res_intercept(self, stream_id: int, client: JAMNP) -> SegmentsShard | None:
        """Intercept [Segment Shard]"""
        buffer = client.stream_buffer[stream_id]

        try:
            data, _ = CE139Response.decode_from(buffer[1:])
            data = cast(CE139Response, data)
            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            logger.info(f"Received CE139 segment shards: {data.s_shards}")

            return data.s_shards

        except Exception as e:
            logger.error(Code.BAD_RESPONSE)
            return None
