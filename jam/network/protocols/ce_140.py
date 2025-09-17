from typing import Tuple
from jam.types.protocol.crypto import Hash
from tsrkit_types import U32, Uint, Bytes, TypedVector

from jam.network.connection import NodeConnection
from jam.network.protocols.ce_139_base import (
    SegmentShardRequestBase,
    Justifications,
    Justification,
)
from jam.network.base.protocol import PrefixType
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.log_setup import logger
from jam.utils.merkle import BMRFunctions

from jam.types.work.shard import SegmentsShard, SegmentShard

from jam.storage.da.segments import SegmentShardsDA
from jam.storage.da.audits import JustificationsDA, AuditShardsDA


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

    def __init__(self):
        super().__init__(PrefixType.CE140)

    def req_intercept(self, stream_id: int, server: NodeConnection):
        """Intercept & Process Erasure-Root, Shard Index & Segment Indices on Assurer"""
        from jam.settings import settings

        buffer = server.stream_buffer[stream_id]

        try:
            request = self.parse_request(buffer[1:])

            d3l = settings.d3l
            audit = settings.audit_da
            ss_da = SegmentShardsDA(d3l)
            audits_da = AuditShardsDA(audit)
            justification_da = JustificationsDA(audit)

            # Fetching segments...
            shards = SegmentsShard([])

            bmrfunctions = BMRFunctions()
            justifications = Justifications([])

            for query in request.queries:
                try:
                    ss_dict = ss_da.get(query.erasure_root)
                    justification = justification_da.get(
                        query.erasure_root, query.shard_index
                    )
                    bs_dict = audits_da.get(query.erasure_root)
                    bundle_shard = bs_dict[query.shard_index]
                    bundle_shard_hash = TypedVector[Bytes](
                        [Bytes(Hash.blake2b(bundle_shard.encode()))]
                    )
                    if query.shard_index in ss_dict.keys():
                        s_dict = ss_dict[query.shard_index]

                        s = TypedVector[Bytes]([])
                        for i in s_dict.keys():
                            s.append(Bytes(s_dict[i].encode()))

                        for index in query.seg_indexes:
                            trace = Justification(
                                bmrfunctions.trace_fn(values=s, index=index).unwrap()
                            )
                            justification.extend(bundle_shard_hash)
                            justification.extend(trace)
                            if index in s_dict.keys():
                                shards.append(s_dict[index])
                            else:
                                raise KeyError("Segment index not found")

                        justifications.append(justification)

                    else:
                        raise KeyError("Shard index not found")

                except Exception as e:
                    logger.error(
                        "Error processing some shard index",
                        error=str(e),
                        error_type=type(e).__name__,
                    )

            # Return requested shards
            msg_a = Bytes(b"")
            for shard in shards:
                msg_a += shard.encode()
            len_a = Uint[32](len(msg_a)).encode()

            server.stream_and_keep_open(len_a, stream_id)
            server.stream_and_keep_open(msg_a, stream_id)

            n = len(justifications)
            for ind, jfn in enumerate(justifications):
                msg_n = jfn.encode()
                len_n = Uint[32](len(msg_n)).encode()
                server.stream_and_keep_open(len_n, stream_id)

                if ind == n - 1:
                    server.stream_and_close(msg_n, stream_id)
                else:
                    server.stream_and_keep_open(msg_n, stream_id)
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
    ) -> Tuple[SegmentsShard, Justifications] | None:
        """Intercept [Segment Shard] and Justification"""
        buffer = client.stream_buffer[stream_id]

        try:
            length = U32.decode(buffer[0:4])
            segments_buf = buffer[4 : 4 + length]
            justifications_buf = buffer[length + 4 :]
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

            justifications = Justifications([])
            while len(justifications_buf) != 0:
                length = U32.decode(justifications_buf[0:4])
                justification = Justification.decode(justifications_buf[4 : length + 4])
                justifications.append(justification)
                justifications_buf = justifications_buf[length + 4 :]

            logger.info(
                "Segment Shards and Justifications received via CE140", peer=client
            )

            return segments, justifications

        except Exception as e:
            logger.error(Code.BAD_RESPONSE, error=e)
            return None
