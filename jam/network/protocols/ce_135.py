import asyncio
from typing import cast

from tsrkit_types import U8
from tsrkit_types.struct import structure
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import Uint, U32
from tsrkit_types.sequences import TypedVector
from jam.logging import logger
from jam.network.connection import NodeConnection
from jam.block.extrinsics.guarantees import ReportGuarantee
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.types.protocol.crypto import Hash

from jam.types.work.manifest import Assurers, Justification
from jam.types.work.shard import SegmentsShard, ShardKey

from jam.storage.da.audits import AuditShardsDA, JustificationsDA
from jam.storage.da.segments import SegmentShardsDA

from jam.utils.merkle import BMRFunctions
from jam.utils.chainspec import chain_config
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

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE135

    async def transmit(self, data: CE135Data):
        """Transmit Work Report from Guarantor to Other Validators"""
        from jam.network.start import node
        msg_a = data.guaranteed_wr.encode()
        len_a = data.len.encode()

        logger.info(
            f"Transmitting Guaranteed Work-Report to {len(node.all_connected)} Validators"
        )

        tasks = []
        try:
            for client in node.all_connected:
                logger.debug("Transmitting report", peer=client)

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
                logger.debug(
                    "Report transmitted to validator",
                    stream_id=stream_id,
                    port=client.port,
                )

            responses = list[bool](await gather_with_exceptions(tasks))

            if responses is not None:
                return responses

        except Exception as e:
            logger.error(
                "Failed to distribute report.",
                error=str(e),
                error_type=type(e).__name__,
            )

    def req_intercept(self, stream_id: int, server: NodeConnection):
        """Intercept & Process Work Report on Validator"""

        buffer = server.stream_buffer[stream_id][1:]

        try:
            logger.info("Received Work Report")
            data = CE135Data.decode(buffer)
            data = cast(CE135Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            # Save extrinsic
            from jam.block.extrinsics.guarantees import wrg_store
            wrg_store.store(data.guaranteed_wr)

            # Save Mappings
            from jam.incore.processor import Processor
            Processor.process_guaranteed_report(data.guaranteed_wr)

            # Send Acknowledgement
            ack = b""
            server.stream_and_close(ack, stream_id)

            logger.info("Sent acknowledgement back to guarantor")

            logger.debug("Fetching assigned shard")
            asyncio.create_task(self._req_shard(data.guaranteed_wr))

        except Exception as e:
            # Stop Streaming
            server.stop_stream(stream_id, 1)

            logger.error(
                "Error processing report",
                guarantor=server,
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__,
            )

    def res_intercept(self, stream_id: int, client: NodeConnection) -> bool:
        """Intercept Acknowledgement"""

        buffer = client.stream_buffer[stream_id]

        if buffer == b"":
            logger.info(
                f"Guaranteed Report received on Guarantor Node.", stream_id=stream_id
            )
            return True

        return False

    @staticmethod
    async def _req_shard(data: ReportGuarantee):
        from jam.settings import settings

        print('re_shard node', settings.validator_index)

        slot = data.slot
        signatures = data.signatures
        assurers = Assurers([sign.validator_index for sign in signatures])

        report = data.report
        if settings.validator_index not in assurers:
            er_root = report.package_spec.erasure_root

            shard_index = settings.get_shard_index(report.core_index)

            from jam.network.protocols.ce_137 import (
                ShardDistributionProtocol,
                CE137Data,
                Query,
            )

            CE137 = ShardDistributionProtocol()

            query = Query(shard_index=shard_index, erasure_root=er_root)
            data = CE137Data(len=U32(len(query.encode())), query=query)

            logger.debug(
                "Requesting Shard",
                shard_index=shard_index,
                erasure_root=er_root.hex()[:16] + "...",
            )
            try:
                responses = await CE137.transmit(data=data, assurers=assurers)
                for shard in responses:
                    # Save Shard
                    if shard is not None:
                        merklizer = BMRFunctions()

                        bundle_shard = shard[0]
                        segments_shard = shard[1]
                        justification = shard[2]

                        # creating leaf
                        bundle_shard_hash = Hash.blake2b(bundle_shard.encode())
                        segments_shard_root = merklizer.wb_merklize(
                            values=segments_shard
                        )
                        shards_key = ShardKey(bundle_shard_hash, segments_shard_root)
                        s = Bytes(shards_key.encode())

                        # verifying justification
                        verification = merklizer.verify_wb_tree(
                            leaf=s,
                            index=shard_index,
                            justification=justification,
                            erasure_root=er_root,
                        )

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
                            from jam.operations.handlers.assurer import assurer
                            assurer.record_shard_assr(report.core_index)

                            wr_hash = Hash.blake2b(report.encode())

                            logger.info(
                                f"📩 Assured work report (Assurer)",
                                wr_hash=wr_hash.hex()[:16] + "...",
                                slot=slot,
                            )

                            break
            except Exception as e:
                logger.error(
                    "Failed to request Full Shard (CE137)",
                    error=str(e),
                    error_type=type(e).__name__,
                )
        else:
            # give assurance for this core & this validator
            from jam.operations.handlers.assurer import assurer
            assurer.record_shard_assr(report.core_index)
            wr_hash = Hash.blake2b(report.encode())

            logger.info(
                f"📩 Assured work report (Secondary Guarantor)",
                wr_hash=wr_hash.hex()[:16] + "...",
                slot=slot,
            )

            # saving justification for shard assigned to itself
            from jam.settings import settings

            er_root = report.package_spec.erasure_root
            shard_index = settings.get_shard_index(report.core_index)
            d3l = settings.d3l
            audit = settings.audit_da

            # Fetch Bundle Shard
            bs_da = AuditShardsDA(audit)
            bs_dict = bs_da.get(er_root)

            # Fetch Segments Shard
            ss_da = SegmentShardsDA(d3l)
            ss_dict = ss_da.get(er_root)
            if shard_index not in ss_dict:
                raise "Shard not found"

            bundle_shard_indices = bs_dict.keys()
            segment_shard_indices = ss_dict.keys()

            if (
                len(bundle_shard_indices) != chain_config.num_validators
                or len(segment_shard_indices) != chain_config.num_validators
            ):
                raise ValueError(
                    f"Length of both type of shards should be {chain_config.num_validators}"
                )

            merklizer = BMRFunctions()
            s = TypedVector[Bytes]([])
            for i in range(chain_config.num_validators):
                bundle_shard_hash = Hash.blake2b(bs_dict[i].encode())
                segment_shard = SegmentsShard(ss_dict[i].shard)
                segments_shard_root = merklizer.wb_merklize(values=segment_shard)
                shards_key = ShardKey(bundle_shard_hash, segments_shard_root)
                s.append(Bytes(shards_key.encode()))

            justification = Justification(
                merklizer.trace_fn(values=s, index=shard_index).unwrap()
            )

            justification_da = JustificationsDA(audit)
            justification_da.put(er_root, shard_index, justification)
