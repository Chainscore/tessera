from tsrkit_types import Uint, U32
from typing import cast

from jam.network.base.quic import QuicProtocol
from jam.network.protocols.ce_139_base import SegmentShardRequestBase, CE139Response
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from tsrkit_types import TypedArray, Bytes

from jam.logging import logger

from jam.network.base.protocol import PrefixType
from jam.types.work.shard import SegmentsShard, SegmentShard
from jam.work_package.stores.segments import SegmentShardsDA


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
    from jam.network.node import Node

    def __init__(self):
        super().__init__(PrefixType.CE139)

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept & Process Erasure-Root, Shard Index & Segment Indices on Assurer"""
        from jam.settings import settings
        buffer = server.stream_buffer[stream_id]

        try:
            request = self.parse_request(buffer[1:])
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
            logger.error(
                "Failed to request shards using ce_139",
                error=str(e),
                error_type=type(e).__name__
            )

    def res_intercept(self, stream_id: int, client: QuicProtocol) -> SegmentsShard | None:
        """Intercept [Segment Shard]"""
        buffer = client.stream_buffer[stream_id]

        try:

            length = U32.decode(buffer[1:5])
            segments_buf = buffer[5:5 + length]
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
                    "Parsed segment",
                    cnt=cnt,
                    stream_id=stream_id,
                    peer=client.peer
                )

            logger.info(f"Received CE139 segment shards.")

            return segments

        except Exception as e:
            logger.error(Code.BAD_RESPONSE, err=str(e))
            return None