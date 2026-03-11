from typing import TYPE_CHECKING

from jam.operations.dispatcher import NodeDispatcher
from jam.utils.task_utils import create_safe_task
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jam.block.extrinsics.assurances import AvailAssurance
from jam.block.extrinsics.guarantees import ReportGuarantee

from tsrkit_types import Bytes, U32, TypedVector

from jam.types.protocol.crypto import Hash
from jam.types.protocol.core import CoreIndex
from jam.types.work.manifest import Assurers, Justification
from jam.types.work.shard import SegmentsShard, ShardKey, ShardIndex

from jam.storage.da.audits import AuditShardsDA, JustificationsDA
from jam.storage.da.segments import SegmentShardsDA

from jam.utils.merkle import BMRFunctions
from jam.utils.chainspec import chain_config
from jam.utils.constants import CORE_COUNT, VALIDATOR_COUNT

if TYPE_CHECKING:
    from jam.jam_node import JamNode


class Assurer(NodeDispatcher):
    _collected: list[bool]

    def __init__(self, jam: "JamNode") -> None:
        super().__init__(jam)
        self._collected = [False] * CORE_COUNT

    def record_shard_assr(self, core_index: int):
        self._collected[core_index] = True
        self.logger.debug("Recorded shard for core", core_index=core_index)

    def get_shard_index(self, core_index: CoreIndex):
        vi = self.settings.validator_index(self.state)
        shard_index = ShardIndex(
            (core_index * chain_config.recovery_threshold + vi) % VALIDATOR_COUNT
        )

        return shard_index

    async def run(self, time_slot: int):

        settings = self.settings
        state = self.state
        logger = self.logger

        settings.update(self.state)
        pref = Bytes("jam_available", "utf-8")

        from jam.network.protocols.ce_141 import CE141Data, Assurance
        from jam.block.extrinsics.assurances import AvailBitField
        from jam.types.protocol.crypto import Ed25519Signature, HeaderHash, Hash

        try:
            # This block must be the same as for which req shard is being called upon
            # All the assurances must be recorded and transmitted for the reports mentioned in block
            latest_block = self.grandpa.load_latest()

            # TODO: Fix Assurances Check Per Block
            pending_reps = state.rho.pending_reps()
            if len(pending_reps) == 0:
                logger.debug("No Pending Reports. Skipping assurances.", slot=int(state.tau))
                self.clear()
                return

            bitfield = AvailBitField(self._collected)
            if any(self._collected):
                header_hash = latest_block.header.hash()
                sign_data = header_hash.encode() + bitfield.encode()

                signr = Ed25519PrivateKey.from_private_bytes(settings.ed25519_private).sign(
                    pref + Hash.blake2b(sign_data).encode()
                )

                assurance = Assurance(
                    anchor_hash=HeaderHash(header_hash),
                    bitfield=bitfield,
                    ed25519_signature=Ed25519Signature(signr),
                )

                val_index = settings.validator_index(state)

                assr_ext = AvailAssurance(
                    anchor=HeaderHash(header_hash),
                    bitfield=bitfield,
                    validator_index=val_index,
                    signature=Ed25519Signature(signr),
                )

                logger.info("Storing self assurance", validator=val_index)

                # Store self-assurance
                self.pool.assurances.store(assr_ext)

                data = CE141Data(assurance=assurance, len=U32(len(assurance.encode())))
                create_safe_task(
                    self.router.dispatch(141, data),
                    name="Assurance Transmit"
                )
            else:
                logger.debug("No shards collected. Skipping assurances.", slot=state.tau)
        except Exception as e:
            logger.error("Failed to transmit assurance", error=e, time_slot=time_slot)
        self.clear()

    def clear(self):
        self._collected = [False] * CORE_COUNT

    async def _req_shard(self, data: ReportGuarantee):
        settings = self.settings
        state = self.state
        logger = self.logger

        validator_index = settings.validator_index(state)

        slot = data.slot
        signatures = data.signatures
        assurers = Assurers([sign.validator_index for sign in signatures])

        report = data.report
        wr_hash = report.hash()

        if validator_index not in assurers:
            er_root = report.package_spec.erasure_root

            shard_index = self.get_shard_index(report.core_index)

            from jam.network.protocols.ce_137 import CE137Data, Query

            try:
                query = Query(shard_index=shard_index, erasure_root=er_root)
                data = CE137Data(len=U32(len(query.encode())), query=query)

                logger.debug(
                    "Requesting Shard",
                    shard_index=shard_index,
                    erasure_root=er_root.hex()[:16] + "...",
                )

                responses = await self.router.dispatch(137, data, assurers=assurers)
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

                        logger.debug(
                            "Shard verification",
                            shard_index=shard_index,
                            er_root=er_root.hex()[:16],
                        )

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
                                wr_hash=wr_hash.hex()[:6] + "...",
                                slot=slot,
                                validator_ind=int(validator_index)
                            )
                            break
                        else:
                            logger.warning(
                                "Shard verification failed",
                                wr_hash=wr_hash.hex()[:6] + "...",
                                slot=slot,
                                validator_ind=int(validator_index)
                            )
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
                wr_hash=wr_hash.hex()[:6] + "...",
                slot=slot,
                validator_ind=int(validator_index)
            )

            # saving justification for shard assigned to itself
            er_root = report.package_spec.erasure_root
            shard_index = self.get_shard_index(report.core_index)
            d3l = settings.d3l
            audit = settings.audit_da

            # Fetch Bundle Shard
            bs_da = AuditShardsDA(audit)
            bs_dict = bs_da.get(er_root)

            # Fetch Segments Shard
            ss_da = SegmentShardsDA(d3l)
            ss_dict = ss_da.get(er_root)
            if shard_index not in ss_dict:
                raise ValueError("Shard not found")

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
                i_idx = ShardIndex(i)  # Convert to ShardIndex for dict access
                bundle_shard_hash = Hash.blake2b(bs_dict[i_idx].encode())
                segment_shard = SegmentsShard(ss_dict[i_idx].shard)
                segments_shard_root = merklizer.wb_merklize(values=segment_shard)
                shards_key = ShardKey(bundle_shard_hash, segments_shard_root)
                s.append(Bytes(shards_key.encode()))

            justification = Justification(
                merklizer.trace_fn(values=s, index=shard_index).unwrap()
            )

            justification_da = JustificationsDA(audit)
            justification_da.put(er_root, shard_index, justification)

