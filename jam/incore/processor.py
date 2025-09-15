import asyncio
from typing import Tuple
import time
from tsrkit_types import ByteArray, Uint, Null, Bytes, U8, TypedVector, U32

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
    Ed25519PrivateKey,
)

from jam.block.extrinsics.guarantees import (
    ReportGuarantee,
    ValidatorSignatures,
    ValidatorSignature,
)

from jam.network.connection import NodeConnection
from jam.network.protocols.ce_134 import Credential

from jam.logging import pvm_logger
from jam.execution.invocations.is_authorized import PsiI
from jam.execution.invocations.refine import PsiR

from jam.types.protocol.core import (
    CoreIndex,
    Gas,
    TimeSlot,
    ExportsRoot,
    ValidatorIndex,
)
from jam.types.protocol.crypto import OpaqueHash, Hash, Ed25519Signature, WorkReportHash
from jam.types.work.execution import WorkDigest, WorkExecResult, RefineLoad, WorkDigests

from jam.types.work.item import WorkItem
from jam.types.work.package import WorkPackage, WorkPackageBundle, WorkPackageSpec
from jam.types.work.manifest import (
    Segments,
    Segment,
    MultiSegments,
    Extrinsics,
    ProvedSegments,
    SegmentIndex,
    Assurers,
    SegmentRootLookup,
)
from jam.types.work.report import WorkReport
from jam.types.work.shard import (
    BundleShardHashes,
    SegmentsShards,
    SegmentsShard,
    SegmentsShardRoots,
    ShardKey,
    BundleShard,
    ShardIndex,
    SegmentShard,
    BundleShardsDict,
    SegShardsDict,
    SegShardDict,
)

from jam.incore.bundler import Bundler
from jam.incore.error import ProcessorError, ProcessorErrorCode as Code
from jam.incore.validator import Validator

from jam.storage.da.audits import AuditShardsDA
from jam.storage.da.mappings import PackageSegmentMap, SegmentErasureMap, ReportHashAssurerMap, ErasureAssurerMap
from jam.storage.da.reports import ReportsDA
from jam.storage.da.segments import SegmentsDA, SegmentShardsDA

from jam.utils.merkle import BMRFunctions
from jam.utils.chainspec import chain_config
from jam.utils.constants import (
    BASIC_ERASURE_SIZE,
    GENESIS_TS,
    SEGMENT_SIZE,
    MAX_WORK_REPORT_SIZE,
    SLOT_PERIOD,
    X,
)

from tests.unit.incore.types import FullVector

# Module-specific logger
logger = pvm_logger

vector: FullVector = FullVector()

class Processor:
    """ "Refinement Engine. Synced upto GP v0.7.0"""
    merklizer: BMRFunctions

    def __init__(self):
        self.merklizer = BMRFunctions()

    async def process(
        self,
        package: WorkPackage,
        core: CoreIndex,
        extrinsics: Extrinsics,
        share_guarantee: bool = True,
    ):
        global vector
        vector = FullVector()
        vector.core_index = core
        vector.work_package = package
        vector.extrinsics = extrinsics

        ts = int((time.time() - GENESIS_TS) //  SLOT_PERIOD)
        from jam.network.protocols.ce_134 import (
            CoreSegment,
            WorkPackageSharing,
            CE134Data,
        )
        from jam.network.protocols.ce_135 import WorkReportDistribution, CE135Data

        logger.debug("Validating work package..")
        validator = Validator()
        validator.validate_wp(package)

        bundler = Bundler()

        # Build Segment Root Lookup Dictionary
        logger.debug("Building lookup dictionary..")
        lookup = bundler.build_lookup(package)

        # Build Work Package Bundle
        logger.debug("Building work package bundle..")
        bundle = await bundler.build_bundle(package, extrinsics)
        vector.bundle = bundle
        vector.import_segs = bundle.import_segments

        guarantee_task = None
        if share_guarantee:
            # Distribute Bundle to other Guarantors CE134
            CE134 = WorkPackageSharing()
            core_segment = CoreSegment(core_index=core, segment_root_map=lookup)
            map_len = U32(len(core_segment.encode()))
            bundle_len = U32(len(bundle.encode()))
            data = CE134Data(
                map_len=map_len,
                work_package_bundle=bundle,
                bundle_len=bundle_len,
                core_segment=core_segment,
            )

            logger.debug("Distributing work package bundle..")

            # Use event loop to distribute bundle parallely
            loop = asyncio.get_running_loop()
            loop.set_task_factory(asyncio.eager_task_factory)

            guarantee_task = loop.create_task(CE134.transmit(data=data))

        # Build Report
        logger.debug("Processing work package bundle..")
        wr, wr_hash = self.process_bundle(core, bundle, lookup)

        if share_guarantee and (guarantee_task is not None):
            # Build Guaranteed WR
            guarantees = await guarantee_task
            logger.debug(f"Processing guarantees..", cnt=len(guarantees))
            guaranteed_wr = self.process_guarantees(wr, wr_hash, guarantees)

            # Distribute Guaranteed Work Report to other validators
            CE135 = WorkReportDistribution()
            r_len = U32(len(guaranteed_wr.encode()))
            data = CE135Data(len=r_len, guaranteed_wr=guaranteed_wr)

            logger.debug("Distributing guaranteed work report..")
            transmit_task = asyncio.create_task(
                CE135.transmit(data=data)
            )
            # acks = await transmit_task

            logger.debug("Saving guaranteed work report mappings..")
            self.process_guaranteed_report(guaranteed_wr)

        vector.work_rep = wr
        vector.rep_hash = wr_hash

        return wr, wr_hash

    @staticmethod
    def item_to_digest(item: WorkItem, result: WorkExecResult, gas: Gas) -> WorkDigest:
        """
        Item to Digest function C defined in Eqn 14.9

        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/1bee001bb501?v=0.7.0
        Args:
            item: WorkItem
            result: WorkExecResult
            gas: Gas
        Returns:
            Work Digest a.k.a. Work Result
        """

        extrinsic_size: Uint = Uint(0)
        for i in item.extrinsic:
            extrinsic_size = extrinsic_size + Uint(i.len)

        payload_hash = Hash.blake2b(bytes(item.payload))

        imports_count: Uint = Uint(len(item.import_segments))
        exports_count: Uint = Uint(item.export_count)
        extrinsic_count: Uint = Uint(len(item.extrinsic))

        refine_load = RefineLoad(
            gas_used=Uint(gas),
            imports=imports_count,
            exports=exports_count,
            extrinsic_count=extrinsic_count,
            extrinsic_size=extrinsic_size,
        )

        digest = WorkDigest(
            service_id=item.service,
            code_hash=item.code_hash,
            payload_hash=payload_hash,
            accumulate_gas=item.accumulate_gas_limit,
            result=result,
            refine_load=refine_load,
        )
        return digest

    def build_report(
        self, b: WorkPackageBundle, c: CoreIndex, sr_lookup: SegmentRootLookup, store: bool = True
    ):
        """
        Work Report Computation function Ξ defined in Eqn 14.12
        To be used by main guarantor

        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/1bab021b2e03?v=0.7.0
        Args:
            b: Work Package Bundle
            c: Core Index
            sr_lookup: Segment Root Lookup
            store: Flag to allow storage
        Returns:
            Work Report
        """

        try:
            # Work Package, p
            p = b.package

            # ------------------------------------------ IS AUTH INVOCATION ------------------------------------------
            # Auth Output o & Gas g
            logger.debug(f"Checking authorization..")
            o, g = PsiI(p, c).execute()
            # ------------------------------------------ -- ---- ---------- ------------------------------------------

            s_result = 0

            def utils_i(j: int) -> Tuple[WorkExecResult, Gas, Segments]:
                """
                Function I defined in Eqn 14.12
                Performs Ordered Accumulation of work items in a package p

                https://graypaper.fluffylabs.dev/#/38c4e62/1b92031b9203?v=0.7.0
                """

                nonlocal s_result
                w = p.items[j]

                l = 0
                k = int(j)
                for i in range(k):
                    l += p.items[i].export_count

                # ------------------------------------------ REFINE INVOCATION ----------------------------------------
                logger.debug(f"Refining Work Item {j}..", payload=p.items[j].payload.hex())
                r, e, u = PsiR(j, p, o, b.import_segments, l).execute()
                # ------------------------------------------ ----------------- ----------------------------------------

                segment = Segment([U8(0)] * SEGMENT_SIZE)
                segment_count = w.export_count
                zero_segments = Segments([segment for _ in range(segment_count)])
                z = len(o) + s_result

                if r.get_key() != "ok":
                    return r, u, zero_segments
                elif z + len(r.unwrap()) > MAX_WORK_REPORT_SIZE:
                    return WorkExecResult({"result_oversize": Null}), u, zero_segments
                elif len(e) != w.export_count:
                    return WorkExecResult({"bad_exports": Null}), u, zero_segments
                else:
                    s_result += len(r.unwrap())
                    return r, u, e

            # Work Digests, r
            r_list = WorkDigests([])

            # Exported Segments
            e_list = MultiSegments([])

            for _j in range(len(p.items)):
                _r, _u, _e = utils_i(_j)

                comp = self.item_to_digest(p.items[_j], _r, _u)
                r_list.append(comp)
                e_list.append(_e)

            # Work Package Hash, h
            h = Hash.blake2b(p.encode())

            # Accumulate all exported segments
            e_bar_cap = Segments([])
            for segments in e_list:
                e_bar_cap.extend(segments)

            logger.debug(f"Exported {len(e_bar_cap)} Segments!")

            # Availability Specification, s
            logger.debug(f"Building availability specification..")
            specs = self.availability_specifier(h, b.encode(), e_bar_cap)

            logger.debug(f"Compiling Report..")
            report = WorkReport(
                package_spec=specs,
                context=p.context,
                core_index=Uint(c),
                authorizer_hash=p.a,
                auth_output=Bytes(o),
                segment_root_lookup=sr_lookup,
                results=r_list,
                auth_gas_used=Uint(g),
            )

            return report

        except Exception as e:
            logger.error(f"Failed to build report", error=e)
            raise

    def availability_specifier(
        self,
        package_hash: OpaqueHash,
        wp_bundle: bytes,
        export_segments: Segments,
        store: bool = True,
    ) -> WorkPackageSpec:
        """
        Availability Specification function defined in Eqn 14.17
        Creates a package specification from the package hash, work-package bundle and the sequence of exported segments

        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/1c24011c0302?v=0.7.0
        Args:
            package_hash (OpaqueHash): Hash of package
            wp_bundle (Bytes): Encoded Audit Bundle
            export_segments (Segments): Exported Segments
            store (bool): A flag to allow process to store formed segments and shards
        Returns:
            s: Availability specifier
        """
        global vector

        from jam.utils.erasure_coding.erasure_code import ErasureCode
        from jam.incore.utils import Utils
        from jam.settings import settings

        utils = Utils()
        try:
            # Work Bundle Length, l
            l = len(wp_bundle)

            # Segment Root, e
            e = ExportsRoot(self.merklizer.cd_merklize(export_segments))
            logger.debug(
                f"Exports Root calculated - {e.hex()}",
                wp_hash=package_hash.hex()[:16] + "...",
            )

            # Segments Count, n
            n = len(export_segments)
            logger.debug("Segments formed", count=n)

            erasure_codec = ErasureCode()

            # Build Bundle Shards
            logger.debug(f"Building bundle shards..")
            padded_wp_bundle = utils.zero_padding(
                ByteArray(wp_bundle), BASIC_ERASURE_SIZE
            )

            bundle_shards = erasure_codec.encode(bytes(padded_wp_bundle))
            logger.debug("Bundle Shards formed", count=len(bundle_shards))

            bs_hashes = BundleShardHashes([])
            bs_dict = BundleShardsDict({})

            for si, bs in enumerate(bundle_shards):
                bs_hash = Hash.blake2b(BundleShard(bs).encode())
                shard_index = ShardIndex(si)
                bundle_shard = BundleShard(bs)
                bs_dict[shard_index] = bundle_shard
                bs_hashes.append(bs_hash)

            proofs = utils.paged_proof(export_segments)

            logger.debug("Proofs formed", count=len(proofs))
            proved_segments = ProvedSegments(segment=export_segments, proof=proofs)

            # Build Segment Shards
            logger.debug(f"Building segment shards..")
            justified_segments: Segments = export_segments
            justified_segments.extend(proofs)

            i = 0
            all_chunks = []
            for item in justified_segments:
                seg_chunks = erasure_codec.encode(item.encode())
                all_chunks.append(seg_chunks)
                logger.debug("Segments Shard formed", count=len(seg_chunks), segment=i)
                i += 1

            segments_shards = SegmentsShards(
                [
                    SegmentsShard(
                        [SegmentShard(all_chunks[j][i]) for j in range(len(all_chunks))]
                    )
                    for i in range(len(all_chunks[0]))
                ]
            )

            ss_roots = SegmentsShardRoots([])
            ss_dict = SegShardsDict({})

            for si, ss in enumerate(segments_shards):
                shard_index = ShardIndex(si)
                s_dict = SegShardDict({})

                for sgi, s in enumerate(ss):
                    segment_index = SegmentIndex(sgi)
                    s_dict[segment_index] = SegmentShard(s)

                ss_root = self.merklizer.wb_merklize(ss)
                ss_dict[shard_index] = s_dict
                ss_roots.append(ss_root)

            # Build Complete Shard Key
            if (
                len(ss_roots) != chain_config.num_validators
                or len(bs_hashes) != chain_config.num_validators
            ):
                raise ValueError(
                    f"Length of both type of shards should be {chain_config.num_validators}"
                )

            shards_keys = TypedVector[Bytes]([])
            for i in range(chain_config.num_validators):
                shards_key = ShardKey(bs_hashes[i], ss_roots[i])
                shards_keys.append(Bytes(shards_key.encode()))

            # Erasure Root
            u = self.merklizer.wb_merklize(shards_keys)
            logger.info(
                f"Erasure Root calculated - {u.hex()}",
                wp_hash=package_hash.hex()[:16] + "...",
            )

            if store:
                logger.debug(f"Storing Segments & Shards")

                # Access DA
                d3l = settings.d3l
                audits = settings.audit_da

                # Store Exported Segments
                seg_da = SegmentsDA(d3l)
                seg_da.put(e, proved_segments)
                logger.debug("Stored segments")

                # Store Bundle Shards
                audits_da = AuditShardsDA(audits)
                audits_da.put_batch(u, bs_dict)
                logger.debug("Stored bundle shards")

                # Store Segment Shards
                s_shards_da = SegmentShardsDA(d3l)
                s_shards_da.put_batch(u, ss_dict)
                logger.debug("Stored segment shards")

            spec = WorkPackageSpec(
                hash=package_hash,
                length=Uint[32](l),
                erasure_root=u,
                exports_root=e,
                exports_count=Uint[16](n),
            )

            logger.info(
                f"Compiled availability specification",
                erasure_root=u.hex(),
                exports_root=e.hex(),
            )

            vector.export_segs = justified_segments
            vector.shards = shards_keys
            vector.ss_roots = ss_roots
            vector.bs_hashes = bs_hashes
            vector.seg_shards = segments_shards
            vector.bun_shards = bundle_shards

            return spec
        except Exception as e:
            logger.error("Failed to build availability specification", error=e)
            raise

    def process_bundle(
        self,
        core: CoreIndex,
        bundle: WorkPackageBundle,
        sr_lookup: SegmentRootLookup,
        store: bool = True,
    ) -> Tuple[WorkReport, WorkReportHash]:
        from jam.settings import settings

        wp_hash = bundle.package.hash()
        try:
            # Generate Report
            logger.debug("Building Work Report..")
            report = self.build_report(bundle, core, sr_lookup, store)

            wr_hash = WorkReportHash(Hash.blake2b(report.encode()))
            logger.info(
                f"Report compiled", wp_hash=wp_hash.hex(), wr_hash=wr_hash.hex()
            )

            if store:
                # Access DA
                d3l = settings.d3l

                # Store Report
                reports_da = ReportsDA(d3l)
                reports_da.put(wr_hash, report)
                logger.debug(
                    f"Stored work report", wp_hash=wp_hash.hex(), wr_hash=wr_hash.hex()
                )

            return report, wr_hash

        except Exception as e:
            logger.error(
                "Failed to process bundle",
                error=e,
                wp_hash=wp_hash.hex(),
                error_type=type(e).__name__,
            )
            raise

    @staticmethod
    def process_guaranteed_report(report_guarantee: ReportGuarantee):
        from jam.settings import settings

        # Store Extrinsic
        from jam.block.extrinsics.guarantees import wrg_store
        wrg_store.store(report_guarantee)

        wr = report_guarantee.report
        wr_hash = Hash.blake2b(wr.encode())

        guarantees = report_guarantee.signatures
        erasure_root = wr.package_spec.erasure_root
        exports_root = wr.package_spec.exports_root

        package_hash = wr.package_spec.hash
        assurers = Assurers([sign.validator_index for sign in guarantees])

        d3l = settings.d3l

        rep_da = ReportsDA(d3l)
        map_da = PackageSegmentMap(d3l)
        sr_er_da = SegmentErasureMap(d3l)
        er_ar_da = ErasureAssurerMap(settings.d3l)
        wr_da = ReportHashAssurerMap(d3l)

        # Store Report Hash -> Report Mapping
        rep_da.put(wr_hash, wr)

        # Store Package Hash -> Segment Root Mapping
        map_da.put(wr)

        # Store Segment Root -> Erasure Root Mapping
        sr_er_da.put(root=exports_root, data=erasure_root)

        # Store Erasure Root -> Report Hash + Assurers Mapping
        er_ar_da.put(wr, assurers)

        # Store Report Hash -> Assurers Mapping
        wr_da.put(wr, assurers)

        logger.debug(
            "Saved guaranteed work report",
            wp_hash=package_hash.hex()[:16] + "...",
            wr_hash=wr_hash.hex()[:16] + "...",
            er_root=erasure_root.hex()[:16] + "...",
            seg_root=exports_root.hex()[:16] + "...",
        )

    def process_guarantees(
        self,
        wr: WorkReport,
        wr_hash: WorkReportHash,
        signatures: list[tuple[Credential | None, NodeConnection]],
    ):
        """
        Function for processing guarantees
        """

        from jam.settings import settings

        ed25519_key = Ed25519PrivateKey.from_private_bytes(settings.ed25519_private)

        payload = X.GUARANTEE.value + wr_hash.encode()

        # Sign the Guarantee
        sign = Ed25519Signature(ed25519_key.sign(payload))

        from jam.settings import settings
        og_guarantee = ValidatorSignature(
            validator_index=ValidatorIndex(settings.validator_index), signature=sign
        )

        # Check majority & Build guarantees:
        guarantees = [og_guarantee]

        for cred, peer in signatures:
            if cred is not None and cred.work_report_hash == wr_hash:
                try:
                    Ed25519PublicKey.from_public_bytes(peer.ed25519_public).verify(
                        cred.ed25519_signature,
                        payload,
                    )

                    guarantee = ValidatorSignature(
                        validator_index=peer.validator_index,
                        signature=cred.ed25519_signature,
                    )

                    guarantees.append(guarantee)
                except InvalidSignature:
                    logger.error("Invalid guarantee received from peer", peer=peer)

        # Sort the guarantees
        guarantees = ValidatorSignatures(
            sorted(guarantees, key=lambda g: g.validator_index)
        )

        guaranteed_wr = ReportGuarantee(
            report=wr,
            slot=TimeSlot((time.time() - GENESIS_TS) // SLOT_PERIOD),
            signatures=guarantees,
        )

        if len(guarantees) < 2:
            raise ProcessorError(Code.INSUFFICIENT_GUARANTEES)

        logger.debug(
            "Processed guarantees",
            wr_hash=wr_hash.hex()[:16] + "...",
        )

        return guaranteed_wr
