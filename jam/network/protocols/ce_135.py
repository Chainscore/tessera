from dataclasses import dataclass
from typing import cast

from rich.diagnose import report

from jam.config.logging import logger
from jam.config.settings import settings
from jam.db.kv import KVStore
from jam.merklization import BMRFunctions
from jam.network.quic.server import QuicServerProtocol
from jam.types import Null, Vector, Int, ValidatorIndex
from jam.types.extrinsics.guarantees import ValidatorSignatures
from jam.types.protocol.crypto import Hash
from jam.types.work.shard import ShardIndex, BundleShardUnit, SegmentsShardUnit

from jam.utils.json import JsonSerde
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.network.protocols.base import NetworkProtocol, PrefixType

from jam.types.work.report import WorkReport
from jam.types.protocol.core import TimeSlot
from jam.work_package.stores.audits import AuditShardsDA
from jam.work_package.stores.mappings import ErasureShardsMap
from jam.work_package.stores.reports import ReportsDA
from jam.work_package.stores.segments import SegmentShardsDA


@decodable_dataclass
@dataclass
class CE135Data(Codable, JsonSerde):
    report: WorkReport
    slot: TimeSlot
    len: Int
    signatures: ValidatorSignatures


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

        message = self._prefix.encode() + data.encode()

        logger.info(f"Transmitting Guaranteed Work-Report to {len(node.connections)} Validators")
        # TODO: Use All Validators Connections

        responses = Vector([])
        for client in node.connections:
            data = await client.stream_and_close(message=message)
            responses.append(data)

        return responses

    async def server_intercept(self, node: Node, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        """Intercept & Process Work Report on Validator (server)"""

        logger.info("Received Work Report")
        data, offset = CE135Data.decode_from(buffer)
        data = cast(CE135Data, data)

        # Send Acknowledgement
        ack = self._prefix.encode()
        server.stream_and_close(stream_id, ack)

        logger.info("Sent acknowledgement back to guarantor")

        logger.info("Fetching assigned shard")

        report = data.report
        wr_hash = Hash.blake2b(report.encode())

        slot = data.slot
        signatures = data.signatures

        er_root = data.report.package_spec.erasure_root
        # TODO: Fix this
        validator_index = ValidatorIndex(0)

        # TODO: Change 342 to Recovery Threshold based on Network Spec
        shard_index = ShardIndex((report.core_index * 342 + validator_index) % settings.VALIDATOR_COUNT)

        from tests.dummy.dummy_package import create_dummy_assurances
        from jam.network.protocols.ce_137 import ShardDistributionProtocol, CE137TransmitData
        CE137 = ShardDistributionProtocol()

        data = CE137TransmitData(shard_index=shard_index, erasure_root=er_root)
        shard =  await CE137.transmit(node=node, data=data)

        # Save Shard
        if shard is not None:
            bmr = BMRFunctions()
            d3l = KVStore(settings.D3L_PATH)

            bs_da = AuditShardsDA(d3l)
            ss_da = SegmentShardsDA(d3l)
            er_shard_map = ErasureShardsMap(d3l)

            bs_hash = Hash.blake2b(shard.bundle_shard)

            bs_u = BundleShardUnit(shard_index=shard_index, shard=shard.bundle_shard)
            bs_da.put(bs_hash, bs_u)

            ss_root = bmr.wb_merkle_fn(shard.segment_shard)
            ss_u = SegmentsShardUnit(shard_index=shard_index, shard=shard.segment_shard)
            ss_da.put(ss_root, ss_u)

            er_shard_map.put(er_root, bs_hash, ss_root, shard_index)

            d3l.close()

        # Distribute Assurance
        from jam.network.protocols.ce_141 import AssuranceDistribution, CE141Data
        CE141 = AssuranceDistribution()

        assurance = create_dummy_assurances()
        data = CE141Data(assurance)
        ack = await CE141.transmit(node=node, data=data)

        # Save Report
        d3l = KVStore(settings.D3L_PATH)

        rep_da = ReportsDA(d3l)
        rep_da.put(wr_hash, report)

        d3l.close()

        logger.info(f"📩 Assured work report : {wr_hash} with slot {slot}")



    def client_intercept(self, node: Node, buffer: bytes, stream_id: int):
        """Intercept Acknowledgement"""

        logger.info(f"Guaranteed Report received on Guarantor Node via stream {stream_id}")
        return Null


