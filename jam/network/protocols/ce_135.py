import asyncio
from typing import cast

from tsrkit_types import Vector, Null, Option, Bool, Uint, TypedVector

from jam.config.logging import logger
from jam.config.settings import settings

from jam.merklization import BMRFunctions
from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.types.block.extrinsics.guarantees import ValidatorSignatures
from jam.types.protocol.core import ValidatorIndex, TimeSlot
from jam.types.protocol.crypto import Hash
from jam.types.work.report import WorkReport
from jam.types.work.shard import ShardIndex, BundleShardUnit, SegmentsShardUnit
from jam.utils import constants

from tsrkit_types.struct import structure

from jam.work_package.stores.audits import AuditShardsDA
from jam.work_package.stores.mappings import ErasureShardsMap
from jam.work_package.stores.reports import ReportsDA
from jam.work_package.stores.segments import SegmentShardsDA

@structure
class GuaranteedWR:
    report: WorkReport
    slot: TimeSlot
    signatures: ValidatorSignatures

@structure
class CE135Data:
    len: Uint[32]
    guaranteed_wr: GuaranteedWR

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
            if int(peer.port) == 30336:
                logger.info("sending report to 30336")
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
        data, offset = CE135Data.decode_from(buffer[1:])
        data = cast(CE135Data, data)

        if not data.is_valid:
            raise NetworkingError(Code.INVALID_DATA)

        # Send Acknowledgement
        ack = self._prefix.encode()
        server.stream_and_close(ack, stream_id)

        logger.info("Sent acknowledgement back to guarantor")

        logger.info("Fetching assigned shard")
        asyncio.create_task(self._req_shard(data.guaranteed_wr, node))


    def res_intercept(self, stream_id: int, client: QuicProtocol) -> OptBool:
        """Intercept Acknowledgement"""
        buffer = client.stream_buffer[stream_id]
        if buffer[1:] == b"":
            logger.info(f"Guaranteed Report received on Guarantor Node via stream {stream_id}")
            return OptBool(True)

        return OptBool(Null)

    @staticmethod
    async def _req_shard(data: GuaranteedWR, node: Node):
        slot = data.slot
        signatures = data.signatures

        er_root = data.report.package_spec.erasure_root
        # TODO: Fix this
        validator_index = ValidatorIndex(4)

        report = data.report

        # TODO: Change 342 to Recovery Threshold based on Network Spec
        shard_index = ShardIndex((report.core_index * 342 + validator_index) % constants.VALIDATOR_COUNT)

        from jam.network.protocols.ce_137 import ShardDistributionProtocol, CE137Data, Query
        CE137 = ShardDistributionProtocol()

        query = Query(shard_index=shard_index, erasure_root=er_root)
        data = CE137Data(len=len(query.encode()), query=query)
        shard = await CE137.transmit(node=node, data=data)

        # Save Shard
        if shard is not None:
            bmr = BMRFunctions()
            d3l = settings.d3l
            audits = settings.audit

            bs_da = AuditShardsDA(audits)
            ss_da = SegmentShardsDA(d3l)
            er_shard_map = ErasureShardsMap(d3l)

            bs_hash = Hash.blake2b(shard.bundle_shard)

            bs_u = BundleShardUnit(shard_index=shard_index, shard=shard.bundle_shard)
            bs_da.put(bs_hash, bs_u)

            ss_root = bmr.wb_merkle_fn(shard.segment_shard)
            ss_u = SegmentsShardUnit(shard_index=shard_index, shard=shard.segment_shard)
            ss_da.put(ss_root, ss_u)

            er_shard_map.put(er_root, bs_hash, ss_root, shard_index)

            # Distribute Assurance
            from jam.network.protocols.ce_141 import AssuranceDistribution, CE141Data
            CE141 = AssuranceDistribution()

            from jam.network.utils.dummy_assurance import create_dummy_assurances
            assurance = create_dummy_assurances()
            data = CE141Data(assurance)
            ack = await CE141.transmit(node=node, data=data)

            # Save Report
            rep_da = ReportsDA(d3l)

            wr_hash = Hash.blake2b(report.encode())
            rep_da.put(wr_hash, report)


            logger.info(f"📩 Assured work report : {wr_hash} with slot {slot}")