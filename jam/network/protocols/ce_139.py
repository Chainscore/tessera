from tsrkit_types import Uint, U32

from jam.network.connection import NodeConnection
from jam.network.protocols.ce_139_base import SegmentShardRequestBase
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from tsrkit_types import Bytes

from jam.log_setup import logger

from jam.network.base.protocol import PrefixType
from jam.types.work.shard import SegmentsShard, SegmentShard
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

    def req_intercept(self, stream_id: int, server: NodeConnection):
        """Intercept & Process Erasure-Root, Shard Index & Segment Indices on Assurer"""
        from jam.settings import settings

        buffer = server.stream_buffer[stream_id][1:]

        try:
            request = self.parse_request(buffer)
            logger.info("Handling CE139 shard request")
            d3l = settings.d3l
            ss_da = SegmentShardsDA(d3l)

            # TODO: optimize by creating map of erasure root to shard index and segment index

            shards = []
            for query in request.queries:
                ss_dict = ss_da.get(query.erasure_root)
                if query.shard_index in ss_dict.keys():
                    s_dict = ss_dict[query.shard_index]
                    for index in query.seg_indexes:
                        if index in s_dict.keys():
                            shards.append(s_dict[index])
                        else:
                            logger.error("Segment index not found")
                else:
                    logger.error("Shard index not found")

            # Return requested shards
            msg_a = Bytes(b"")
            for shard in shards:
                msg_a += shard.encode()
            len_a = Uint[32](len(msg_a)).encode()

            server.stream_and_keep_open(len_a, stream_id)
            server.stream_and_close(msg_a, stream_id)

        except Exception as e:
            # Stop Streaming
            server.stop_stream(stream_id, 1)

            logger.error(
                "Failed to handle shard request via CE140",
                error=str(e),
                error_type=type(e).__name__,
            )

    def res_intercept(
        self, stream_id: int, client: NodeConnection
    ) -> SegmentsShard | None:
        """Intercept [Segment Shard]"""
        buffer = client.stream_buffer[stream_id]

        try:
            length = U32.decode(buffer[0:4])
            segments_buf = buffer[4 : 4 + length]
            buf_len = len(segments_buf)

            if not segments_buf or not buf_len == length:
                raise NetworkingError(Code.INVALID_DATA)

            offset = 0
            cnt = 0
            segments = SegmentsShard([])
            while offset < buf_len:
                segment, off = SegmentShard.decode_from(segments_buf, offset)
                offset += off
                segments.append(segment)
                cnt += 1
                logger.debug(
                    "Parsed segment", cnt=cnt, stream_id=stream_id, peer=client
                )

            logger.info("Segment Shards received via CE139", peer=client)

            return segments

        except Exception as e:
            logger.error(Code.BAD_RESPONSE, err=str(e))
            return None
