import asyncio
from typing import cast
from jam.operations import assr_collector
from tsrkit_types import Null, Option, Bool, Uint, TypedVector, U32, structure, Bytes

from jam.logging import logger

from jam.storage.stores import guarantee_store
from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.types.block.extrinsics.guarantees import ReportGuarantee, ValidatorSignatures
from jam.types.protocol.core import ValidatorIndex, TimeSlot
from jam.types.protocol.crypto import Hash
from jam.types.work.manifest import Assurers
from jam.types.work.report import WorkReport

from jam.work_package.stores.audits import AuditShardsDA, JustificationsDA
from jam.work_package.stores.reports import ReportsDA
from jam.work_package.stores.segments import SegmentShardsDA
from jam.work_package.stores.mappings import ReportHashAssurerMap, ErasureAssurerMap
from jam.merklization import BMRFunctions
from jam.types.work.shard import ShardKey
from jam.utils.gather import gather_with_exceptions

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

        tasks = TypedVector([])
        try:
            for peer in node.peer_conn:
                logger.debug("Sending report to:", port=peer.port)
                client = node.peer_conn[peer][1]

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                res = client.close_and_wait(message=msg_a, stream_id=stream_id)
                task = asyncio.create_task(res)
                tasks.append(task)
                logger.debug(
                    "Report transmitted to validator",
                    stream_id=stream_id,
                    port=peer.port,
                )

            responses = TypedVector[OptBool](await gather_with_exceptions(tasks))

            if responses is not None:
                return responses

        except Exception as e:
            logger.error(
                "Failed to distribute report.",
                error=str(e),
                error_type=type(e).__name__
            )

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
        from jam.operations.ext_store import ext_store
        ext_store.import_rg(data.guaranteed_wr)

        # save assurers
        assurers = Assurers([])
        for i in data.guaranteed_wr.signatures:
            assurers.append(i.validator_index)

        from jam.settings import settings
        # report hash to assurers mapping
        wr_da = ReportHashAssurerMap(settings.d3l)
        wr_da.put(data.guaranteed_wr.report, assurers)

        # erasure root to report hash & assurers mapping
        er_da = ErasureAssurerMap(settings.d3l)
        er_da.put(data.guaranteed_wr.report, assurers)

        # Send Acknowledgement
        ack = self._prefix.encode()
        server.stream_and_close(ack, stream_id)

        logger.info("Sent acknowledgement back to guarantor")

        logger.info("Fetching assigned shard")
        asyncio.create_task(self._req_shard(data.guaranteed_wr, node, assurers))


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
    async def _req_shard(data: ReportGuarantee, node: Node, assurers: Assurers):
        from jam.settings import settings

        slot = data.slot
        signatures = data.signatures

        report = data.report
        if node.validator_index not in assurers:
            er_root = report.package_spec.erasure_root

            shard_index = node.get_shard_index(report.core_index)

            from jam.network.protocols.ce_137 import ShardDistributionProtocol, CE137Data, Query
            CE137 = ShardDistributionProtocol()

            query = Query(shard_index=shard_index, erasure_root=er_root)
            data = CE137Data(len=U32(len(query.encode())), query=query)

            logger.debug("Requesting Shard", shard_index=shard_index, erasure_root=er_root)

            try:
                responses = await CE137.transmit(node=node, data=data, assurers=assurers)
                for shard in responses:
                    # Save Shard
                    if shard is not None:
                        bmrfunctions = BMRFunctions()

                        bundle_shard = shard[0]
                        segments_shard = shard[1]
                        justification = shard[2]

                        # creating leaf
                        bundle_shard_hash = Hash.blake2b(bundle_shard.encode())
                        segments_shard_root = bmrfunctions.wb_merkle_fn(values=segments_shard)
                        shards_key = ShardKey(bundle_shard_hash, segments_shard_root)
                        s = Bytes(shards_key.encode())

                        # verifying justification
                        verification = bmrfunctions.verify_wb_merkle(leaf=s, index=shard_index, justification=justification, erasure_root=er_root)

                        # if verification == True save shards, justification and break out of loop else move to shards provided by other guarantors
                        if verification:
                            # Store Bundle Shard
                            audits = settings.audit_da
                            bs_da = AuditShardsDA(audits)
                            bs_da.put(er_root, shard_index, shard[0])

                            # Store Segments Shard
                            d3l = settings.d3l
                            ss_da = SegmentShardsDA(d3l)
                            ss_da.put(er_root, shard_index, shard[1])

                            # store justification
                            justification_da = JustificationsDA(audits)
                            justification_da.put(er_root, shard_index, justification)

                            # give assurance for this core & this validator
                            from jam.operations.assr_collector import assr_collector
                            assr_collector.record_shard_assr(report.core_index)

                            # Save Report
                            rep_da = ReportsDA(d3l)
                            wr_hash = Hash.blake2b(report.encode())
                            rep_da.put(wr_hash, report)


                            logger.info(f"📩 Assured work report : {wr_hash} with slot {slot}")

                            break
            except Exception as e:
                logger.error(
                    "Failed to request shards using ce_137",
                    error=str(e),
                    error_type=type(e).__name__
                )
        else:
            # give assurance for this core & this validator
            from jam.operations.assr_collector import assr_collector
            assr_collector.record_shard_assr(report.core_index)