import asyncio
from typing import cast
from tsrkit_types import Null, Option, Bool, Uint, TypedVector, U32, structure

from jam.logging import logger

from jam.storage.stores import guarantee_store
from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.types.block.extrinsics.guarantees import ReportGuarantee, ValidatorSignatures
from jam.types.protocol.core import ValidatorIndex, TimeSlot
from jam.types.protocol.crypto import Hash
from jam.types.work.report import WorkReport

from jam.work_package.stores.audits import AuditShardsDA
from jam.work_package.stores.reports import ReportsDA
from jam.work_package.stores.segments import SegmentShardsDA


@structure
class CE135Data:
    len: Uint[32]
    guaranteed_wr: ReportGuarantee

    @property
    def is_valid(self):
        if len(self.guaranteed_wr.encode()) == self.len:
            return True
        return False


OptBool = Option[Bool]

class WorkReportDistribution(NetworkProtocol):
    """
    CE 135 Protocol for distributing Guaranteed Work Report

    Protocol Flow:
        Guarantor -> Validator

        --> Guaranteed Work-Report
        --> FIN
        <-- FIN
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-135-work-report-distribution
    """

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE135

    async def transmit(self, node: Node, data: CE135Data):
        """Transmit Work Report from Guarantor (client) to Validator (server)"""

        msg_a = data.guaranteed_wr.encode()
        len_a = data.len.encode()

        logger.info(f"Transmitting Guaranteed Work-Report to {len(node.peer_conn)} Validators")
        # TODO: Use All Validators Connections

        responses = TypedVector[OptBool]([])
        for peer in node.peer_conn:
            logger.debug("Sending report to 40003")
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
        """Intercept & Process Work Report on Validator (server)"""
        node = server.node
        buffer = server.stream_buffer[stream_id]

        logger.info("Received Work Report")
        data = CE135Data.decode(buffer[1:])
        data = cast(CE135Data, data)

        if not data.is_valid:
            raise NetworkingError(Code.INVALID_DATA)

        # Save extrinsic
        from jam.consensus.ext_store import ext_store
        ext_store.import_rg(data.guaranteed_wr)

        # Send Acknowledgement
        ack = self._prefix.encode()
        server.stream_and_close(ack, stream_id)

        logger.info("Sent acknowledgement back to guarantor")

        logger.info("Fetching assigned shard")
        # asyncio.create_task(self._req_shard(data.guaranteed_wr, node))


    def res_intercept(self, stream_id: int, client: QuicProtocol) -> OptBool:
        """Intercept Acknowledgement"""
        buffer = client.stream_buffer[stream_id]
        if buffer[1:] == b"":
            logger.info(
                f"Guaranteed Report received on Guarantor Node.",
                stream_id=stream_id
            )
            return OptBool(True)

        return OptBool(Null)

    @staticmethod
    async def _req_shard(data: ReportGuarantee, node: Node):
        from jam.settings import settings

        slot = data.slot
        signatures = data.signatures

        report = data.report
        er_root = report.package_spec.erasure_root

        shard_index = node.get_shard_index(report.core_index)

        from jam.network.protocols.ce_137 import ShardDistributionProtocol, CE137Data, Query
        CE137 = ShardDistributionProtocol()

        query = Query(shard_index=shard_index, erasure_root=er_root)
        data = CE137Data(len=U32(len(query.encode())), query=query)

        logger.debug("Requesting Shard", shard_index=shard_index, erasure_root=er_root)
        shard = await CE137.transmit(node=node, data=data)

        # Save Shard
        if shard is not None:
            # Store Bundle Shard
            audits = settings.audit_da
            bs_da = AuditShardsDA(audits)
            bs_da.put(er_root, shard_index, shard[0])

            # Store Segments Shard
            d3l = settings.d3l
            ss_da = SegmentShardsDA(d3l)
            ss_da.put(er_root, shard_index, shard[1])

            # give assurance for this core
            from jam.operations.assr_collector import assr_collector
            assr_collector.record_shard_assr(report.core_index)

            # Save Report
            rep_da = ReportsDA(d3l)
            wr_hash = Hash.blake2b(report.encode())
            rep_da.put(wr_hash, report)


            logger.info(f"📩 Assured work report : {wr_hash} with slot {slot}")