from jam.utils.task_utils import create_safe_task
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jam.block.extrinsics.assurances import AvailAssurance
from jam.block.extrinsics.guarantees import ReportGuarantee
from jam.log_setup import node_logger as logger

from tsrkit_types import Bytes, U32, TypedVector

from jam.types.protocol.crypto import Hash
from jam.types.work.manifest import Assurers, Justification
from jam.types.work.shard import SegmentsShard, ShardKey

from jam.storage.da.audits import AuditShardsDA, JustificationsDA
from jam.storage.da.segments import SegmentShardsDA

from jam.utils.merkle import BMRFunctions
from jam.utils.chainspec import chain_config
from jam.utils.constants import CORE_COUNT


class Assurer:
    _collected: list[bool]

    def __init__(self) -> None:
        self._collected = [False] * CORE_COUNT

    def record_shard_assr(self, core_index: int):
        self._collected[core_index] = True
        logger.debug("Recorded shard for core", core_index=core_index)

    async def run(self, time_slot: int):
        from jam.settings import settings
        settings.update()
        pref = Bytes("jam_available", "utf-8")

        from jam.network.protocols.ce_141 import CE141Data, AssuranceDistribution
        from jam.finality.finality import Finality
        from jam.network.protocols.ce_141 import Assurance
        from jam.state.state import state

        from jam.block.extrinsics.assurances import AvailBitField
        from jam.types.protocol.crypto import Ed25519Signature, HeaderHash, Hash

        try:
            # This block must be the same as for which req shard is being called upon
            # All the assurances must be recorded and transmitted for the reports mentioned in block
            latest_block = Finality.load_latest(kv=settings.main_db)

            # TODO: Fix Assurances Check Per Block
            pending_reps = state.rho.pending_reps()
            if len(pending_reps) == 0:
                logger.debug("No Pending Reports. Skipping assurances.", slot=state.tau)
                self.clear()
                return

            bitfield= AvailBitField(self._collected)
            header_hash = latest_block.header.hash()
            sign_data = header_hash.encode() + bitfield.encode()

            signr = Ed25519PrivateKey.from_private_bytes(settings.ed25519_private).sign(
                pref + Hash.blake2b(sign_data).encode()
            )

            CE141 = AssuranceDistribution()
            assurance = Assurance(
                anchor_hash=HeaderHash(header_hash),
                bitfield=bitfield,
                ed25519_signature=Ed25519Signature(signr),
            )

            assr_ext = AvailAssurance(
                anchor=HeaderHash(header_hash),
                bitfield=bitfield,
                validator_index=settings.validator_index,
                signature=Ed25519Signature(signr),
            )

            logger.info(
                "Storing self assurance",
                validator=settings.validator_index,
                assurance=assr_ext.to_json(),
            )

            # Store self-assurance
            from jam.block.extrinsics.assurances import asr_store
            asr_store.store(assr_ext)

            data = CE141Data(assurance=assurance, len=U32(len(assurance.encode())))
            create_safe_task(CE141.transmit(data=data), name="assurance_transmit")
        except Exception as e:
            logger.error("Failed to transmit assurance", error=e, time_slot=time_slot)
        self.clear()

    def clear(self):
        self._collected = [False] * CORE_COUNT

    async def _req_shard(self, data: ReportGuarantee):
        from jam.settings import settings
        validator_index = settings.validator_index

        slot = data.slot
        signatures = data.signatures
        assurers = Assurers([sign.validator_index for sign in signatures])

        report = data.report
        wr_hash = report.hash()

        if validator_index not in assurers:
            er_root = report.package_spec.erasure_root

            shard_index = settings.get_shard_index(report.core_index)

            from jam.network.protocols.ce_137 import (
                ShardDistributionProtocol,
                CE137Data,
                Query,
            )

            CE137 = ShardDistributionProtocol()

            try:
                query = Query(shard_index=shard_index, erasure_root=er_root)
                data = CE137Data(len=U32(len(query.encode())), query=query)

                logger.debug(
                    "Requesting Shard",
                    shard_index=shard_index,
                    erasure_root=er_root.hex()[:16] + "...",
                )

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
                            self.record_shard_assr(report.core_index)

                            logger.info(
                                f"📩 Assured work report (Assurer)",
                                wr_hash=wr_hash.hex()[:16] + "...",
                                slot=slot,
                                validator_ind=validator_index
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
            self.record_shard_assr(report.core_index)

            logger.info(
                f"📩 Assured work report (Core Guarantor)",
                wr_hash=wr_hash.hex()[:16] + "...",
                slot=slot,
                validator_ind=validator_index
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


assurer = Assurer()
