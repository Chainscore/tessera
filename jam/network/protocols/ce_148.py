import asyncio
from typing import cast, Tuple, Any

from jam.types.protocol.core import SegmentRoot
from tsrkit_types import Uint, structure, TypedVector, U8

from jam.network.connection import PeerConnection
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.types.work.manifest import SegmentJfns, Assurers, SegmentIndex, Segments, SegmentJfn

from jam.network.base.protocol import NetworkProtocol, PrefixType

from jam.storage.da import SegmentsDA

from jam.utils.merkle import BMRFunctions
from jam.utils.gather import gather_with_exceptions

SegmentIndexes = TypedVector[SegmentIndex]

@structure
class Query:
    segment_root: SegmentRoot
    seg_indices: SegmentIndexes

class Queries(TypedVector[Query]):
    def hex(self):
        roots = []
        for query in self:
            roots.append(
                f"({query.segment_root.hex()[:8]}... [{','.join(str(i) for i in query.seg_indices)}]), "
            )

        return roots

@structure
class CE148Data:
    q_len: Uint[32]
    queries: Queries

    @property
    def is_valid(self):
        if len(self.queries.encode()) == self.q_len:
            return True
        return False

@structure
class CE148Response:
    s_len: Uint[32]
    segments: Segments
    p_len: Uint[32]
    proofs: SegmentJfns

    @property
    def is_valid(self):
        if (
            len(self.segments.encode()) == self.s_len
            and len(self.proofs.encode()) == self.p_len
        ):
            return True
        return False


class SegmentRequestProtocol(NetworkProtocol):
    """
    CE 148 Protocol for segment request

    Guarantor -> Guarantor

    --> [Segments-Root ++ len++[Segment Index]]
    --> FIN
    <-- [Segment]
    <-- [Import Proof]
    <-- FIN

    Source:
        https://docs.jamcha.in/advanced/simple-networking/spec#ce-148-segment-request
    """

    # TODO: Handle Errors on granular level: per segment query
    _prefix = PrefixType.CE148

    async def transmit(self, data: CE148Data, assurers: Assurers = None):
        """Transmit Segment Root and Shard Indices Queries from Guarantor/Builder to Guarantors"""
        node = self.jam.router.node

        queries = data.queries
        msg_a = data.queries.encode()
        len_a = data.q_len.encode()

        self.logger.info(
            "Requesting segments form guarantors",
        )

        tasks = TypedVector([])

        try:
            for client in node.all_connected:
                if assurers and len(assurers) and client.validator_index not in assurers:
                    continue

                self.logger.debug(
                    "Requesting audit shard",
                    peer=client,
                    queries=queries.hex(),
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
            self.logger.error(
                "Failed to request audit shard.",
                queries=queries.hex(),
                error=str(e),
                error_type=type(e).__name__,
            )


    async def req_intercept(self, stream_id: int, server: "PeerConnection"):
        """Intercept & Process Segment Queries on Guarantor"""
        settings = self.jam.settings

        buffer = server.stream_buffer[stream_id][1:]
        self.logger.debug("Received segments")

        try:
            data = CE148Data.decode(buffer)
            data = cast(CE148Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            merklizer = BMRFunctions()

            d3l = settings.d3l
            seg_da = SegmentsDA(d3l)

            segments = Segments([])
            proofs = SegmentJfns([])

            for query in data.queries:
                s_root = query.segment_root
                indices = query.seg_indices


                # Fetch Segments
                try:
                    segs, proof_segs = seg_da.get(s_root)
                except KeyError:
                    raise NetworkingError(Code.DATA_UNAVAILABLE)

                n = len(segs)
                for i in indices:
                    if i >= n:
                        raise NetworkingError(Code.INVALID_QUERY)

                    seg = segs[i]
                    proof = merklizer.subtree_path(segs, 1, i).unwrap32()

                    segments.append(seg)
                    proofs.append(SegmentJfn(proof))


            # Return requested shards
            msg_a = segments.encode()
            len_a = Uint[32](len(msg_a)).encode()
            msg_b = proofs.encode()
            len_b = Uint[32](len(msg_b)).encode()

            server.stream_and_keep_open(len_a, stream_id)
            server.stream_and_keep_open(msg_a, stream_id)
            server.stream_and_keep_open(len_b, stream_id)
            server.stream_and_close(msg_b, stream_id)

        except Exception as e:
            # Stop Streaming
            server.stop_stream(stream_id, 1)

            self.logger.error(
                "Failed to find requested segments.", error=str(e), error_type=type(e).__name__
            )

    async def res_intercept(
            self, stream_id: int, client: "PeerConnection"
    ) -> Tuple[Segments, SegmentJfns] | None:
        """Intercept Segments and their Justifications"""

        buffer = client.stream_buffer[stream_id]

        try:
            data = CE148Response.decode(buffer)
            data = cast(CE148Response, data)

            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            self.logger.debug("Requested segments received", peer=client)

            return data.segments, data.proofs

        except Exception as e:
            self.logger.error(Code.BAD_RESPONSE, error=str(e))
            return None