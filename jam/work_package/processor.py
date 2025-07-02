import asyncio
from math import ceil
from typing import Tuple

from tsrkit_types import ByteArray, Uint, Null, Bytes, U8, U16, U64, TypedVector, U32

from jam.utils.chainspec import chain_config
from jam.logging import get_logger

from jam.execution.host_calls.invocations.is_authorized import PsiI
from jam.execution.host_calls.invocations.refine import PsiR

from jam.types.block.extrinsics.guarantees import ValidatorSignatures, ValidatorSignature

from jam.types.protocol.core import CoreIndex, Gas, TimeSlot, ExportsRoot, ValidatorIndex
from jam.types.protocol.crypto import OpaqueHash, Hash, Ed25519Signature, WorkReportHash

from jam.types.work import WorkReport, SegmentRootLookup, WorkPackageSpec, WorkResults
from jam.types.work.item import WorkItem
from jam.types.work.package import WorkPackage, WorkPackageBundle
from jam.types.work.manifest import (
    Segments,
    Segment,
    MultiSegments,
    Extrinsics,
    ProvedSegments, SegmentIndex
)
from jam.types.work.shard import (
    BundleShardHashes,
    SegmentsShards,
    SegmentsShard,
    SegmentsShardRoots,
    ShardKey, BundleShard, ShardIndex, SegmentShard, BundleShardsDict, SegShardsDict, SegShardDict
)
from jam.types.work.execution import (
    WorkResult,
    WorkExecResult,
    RefineLoad
)

from jam.utils.benchmark import benchmark

from jam.utils.constants import BASIC_ERASURE_SIZE, SEGMENT_SIZE, MAX_WORK_REPORT_SIZE

from jam.work_package.stores.mappings import PackageSegmentMap, SegmentErasureMap

from jam.merklization.binary_merkle import BMRFunctions


from jam.work_package.bundler import Bundler
from jam.work_package.stores.audits import AuditShardsDA
from jam.work_package.stores.reports import ReportsDA
from jam.work_package.stores.segments import SegmentsDA, SegmentShardsDA
from jam.work_package.validator import Validator

from jam.network.node import Node

# Module-specific logger
logger = get_logger("in_core")

class Processor:

    node: Node
    merkle: BMRFunctions
    def __init__(self, node: Node):
        from jam.settings import settings
        self.settings = settings
        self.merkle = BMRFunctions()
        self.node = node
        self.transmit_task = None

    @staticmethod
    def zero_padding(value: ByteArray, n: Uint):
        """
        Zero Padding function P defined in Eqn 14.17
        Ensures that the length of individual byte array becomes a multiple of a given integer n.

        Source:
            https://graypaper.fluffylabs.dev/#/cc517d7/1c08011c2d01?v=0.6.5
        Args:
            value (ByteArray) : Octet Array to be padded.
            n (Int) : The target block size. Each element will be padded to a length that is a multiple of n
        Returns:
            New list containing padded byte arrays. Each element's length is now a multiple of n, padded with zeroes at the end.
        """

        length = len(value)
        padding = n - (((length + n - 1) % n) + 1)

        for i in range(padding):
            value.append(0)

        return value

    def paged_proof(self, segments: Segments) -> Segments:
        """
        Page Proof function P defined in Eqn 14.10
        Compiles Justifications for exported segments

        Source:
            https://graypaper.fluffylabs.dev/#/cc517d7/1b2a001b8b00?v=0.6.5
        Args:
            segments (Segments): List of exported segments
        Returns:
            Proofs of size same as segments
        """
        page_count = ceil(len(segments)/64)

        pages: Segments = Segments([])
        for x in range(page_count):
            path = self.merkle.merkle_path_fn(values=segments, size=6, index=x)
            leaf = self.merkle.leaf_page_fn(values=segments, size=6, index=x)
            merkle_path = bytes(len(path)) + path.encode()
            leaf =  bytes(len(leaf)) + leaf.encode()

            segment_proof = Segment(self.zero_padding(ByteArray(merkle_path + leaf), SEGMENT_SIZE))
            pages.append(segment_proof)

        return pages

    @staticmethod
    def item_to_digest(item: WorkItem, result: WorkExecResult, gas: Gas) -> WorkResult:
        """
        Item to Digest function C defined in Eqn 14.8

        Source:
            https://graypaper.fluffylabs.dev/#/cc517d7/1a6a011a5002?v=0.6.5
        Args:
            item: WorkItem
            result: WorkExecResult
            gas: Gas
        Returns:
            Work Digest
        """
        extrinsic_size: Uint = Uint(0)
        for i in item.extrinsic:
            extrinsic_size = extrinsic_size + Uint(i.len)

        payload_hash = Hash.blake2b(bytes(item.payload))

        imports_count: Uint = Uint(len(item.import_segments))
        exports_count: Uint = Uint(item.export_count)
        extrinsic_count: Uint = Uint(len(item.extrinsic))

        refine_load = RefineLoad(gas_used=Uint(gas), imports=imports_count, exports=exports_count,
                                 extrinsic_count=extrinsic_count, extrinsic_size=extrinsic_size)

        result = WorkResult(service_id=item.service, code_hash=item.code_hash, payload_hash=payload_hash,
                          accumulate_gas=item.accumulate_gas_limit, result=result, refine_load=refine_load)
        return result

    def build_report(self, b: WorkPackageBundle, c: CoreIndex, sr_lookup: SegmentRootLookup):
        """
        Work Report Computation function Ξ defined in Eqn 14.11
        To be used by main guarantor

        Source:
            https://graypaper.fluffylabs.dev/#/68eaa1f/1b7c001be700?v=0.6.4
        Args:
            b: Work Package Bundle
            c: Core Index
            sr_lookup: Segment Root Lookup
        Returns:
            Work Report
        """
        try:
            # Work Package, p
            p = b.package

            # ------------------------------------------ IS AUTH INVOCATION ------------------------------------------
            logger.info(f"Checking authorization..")
            # Auth Output o & Gas g
            with benchmark("auth check done"):
                o, g = PsiI(p, c).execute()
            # ------------------------------------------ -- ---- ---------- ------------------------------------------
            s_result = 0

            def utils_i(j: int) -> Tuple[WorkExecResult, Gas, Segments]:
                """
                Function I defined in Eqn 14.11
                Performs Ordered Accumulation of work items in a package p

                https://graypaper.fluffylabs.dev/#/cc517d7/1b3f011b8d01?v=0.6.5
                """

                nonlocal s_result
                w = p.items[j]

                l = 0
                k = int(j)
                for i in range(k):
                    l += p.items[i].export_count

                # ------------------------------------------ REFINE INVOCATION ------------------------------------------
                logger.info(f"Refining Work Item {j}..")
                with benchmark(f"Refined Work Item {j}"):
                    r, e, u = PsiR(j, p, o, b.import_segments, l).execute()
                # ------------------------------------------ ----------------- ------------------------------------------

                segment = Segment([U8(0)] * SEGMENT_SIZE)
                segment_count = w.export_count
                zero_segments = Segments([segment for _ in range(segment_count)])
                z = len(o) + s_result

                if r._choice_key != "ok":
                    return r, u, zero_segments
                elif z + len(r.unwrap()) > MAX_WORK_REPORT_SIZE:
                    return WorkExecResult({"result_oversize": Null}), u, zero_segments
                elif len(e) != w.export_count:
                    return WorkExecResult({"bad_exports": Null}), u, zero_segments
                else:
                    s_result += len(r.unwrap())
                    return r, u, e


            # Work Results, r
            r_list = WorkResults([])

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

            logger.info(f"Exported {len(e_bar_cap)} Segments!")

            # Availability Specification, s
            logger.info(f"Building availability specification..")
            with benchmark("specification built"):
                specs = self.availability_specifier(package_hash=h, wp_bundle=b.encode(), export_segments=e_bar_cap)

            logger.info(f"Compiling Report..")
            report = WorkReport(package_spec=specs, context=p.context, core_index=Uint(c), authorizer_hash=p.a, auth_output=Bytes(o), segment_root_lookup=sr_lookup, results=r_list, auth_gas_used=Uint(g))

            return report

        except Exception as e:
            logger.error(f"Failed to build report", error=e)
            raise


    def availability_specifier(self, package_hash: OpaqueHash, wp_bundle: bytes, export_segments: Segments) -> WorkPackageSpec:
        """
        Availability Specification function defined in Eqn 14.16
        Creates a package specification from the package hash, work-package bundle and the sequence of exported segments

        Source:
            https://graypaper.fluffylabs.dev/#/cc517d7/1c3a001cf000?v=0.6.5
        Args:
            package_hash (OpaqueHash): Hash of package
            wp_bundle (Bytes): Encoded Audit Bundle
            export_segments (Segments): Exported Segments
        Returns:
            s: Availability specifier
        """
        from jam.erasure_coding.erasure_code import ErasureCode
        settings = self.settings

        try:
            # Work Bundle Length, l
            l = len(wp_bundle)

            # Segment Root, e
            e = ExportsRoot(self.merkle.cd_merkle_fn(export_segments))
            logger.info(f"Exports Root calculated - {e.hex()} {e}")

            # Segments Count, n
            n = len(export_segments)
            logger.debug("Segments formed", count=n)

            erasure_codec = ErasureCode()

            # Build Bundle Shards
            logger.info(f"Building bundle shards..")

            with benchmark("Bundle Padded"):
                padded_wp_bundle = self.zero_padding(ByteArray(wp_bundle), BASIC_ERASURE_SIZE)

            with benchmark("Erasure Coded Bundle"):
                bundle_shards = erasure_codec.encode(bytes(padded_wp_bundle))
                logger.debug("Bundle Shards formed", count=len(bundle_shards))

            bs_hashes = BundleShardHashes([])
            bs_dict = BundleShardsDict({})

            with benchmark("Processed bundle chunks"):
                for si, bs in enumerate(bundle_shards):
                    bs_hash = Hash.blake2b(BundleShard(bs).encode())
                    shard_index = ShardIndex(si)
                    bundle_shard = BundleShard(bs)
                    bs_dict[shard_index] = bundle_shard
                    bs_hashes.append(bs_hash)

            with benchmark("Built proofs"):
                proofs = self.paged_proof(export_segments)
                logger.debug("Proofs formed", count=len(proofs))
                proved_segments = ProvedSegments(segment=export_segments, proof=proofs)


            # Build Segment Shards
            logger.info(f"Building segment shards..")
            justified_segments: Segments = export_segments
            justified_segments.extend(proofs)


            with benchmark("Erasure coded segments"):
                i = 0
                all_chunks = []
                for item in justified_segments:
                    seg_chunks = erasure_codec.encode(item.encode())
                    all_chunks.append(seg_chunks)
                    logger.debug("Segments Shard formed", count=len(seg_chunks), segment=i)
                    i += 1

            with benchmark("Transposed segment shards"):
                segments_shards = SegmentsShards(
                    [
                        SegmentsShard(
                            [
                                SegmentShard(all_chunks[j][i]) for j in range(len(all_chunks))
                            ]
                        ) for i in range(len(all_chunks[0]))
                    ]
                )

            ss_roots = SegmentsShardRoots([])
            ss_dict = SegShardsDict({})

            with benchmark("Processed segment chunks"):
                for si, ss in enumerate(segments_shards):
                    shard_index = ShardIndex(si)
                    s_dict = SegShardDict({})

                    for sgi, s in enumerate(ss):
                        segment_index = SegmentIndex(sgi)
                        s_dict[segment_index] = SegmentShard(s)

                    ss_root = self.merkle.wb_merkle_fn(ss)
                    ss_dict[shard_index] = s_dict
                    ss_roots.append(ss_root)

            # Build Complete Shard Key
            if len(ss_roots) != chain_config.num_validators or len(bs_hashes) != chain_config.num_validators:
                raise ValueError(f"Length of both type of shards should be {chain_config.num_validators}")

            shards_keys = TypedVector[Bytes]([])
            for i in range(chain_config.num_validators):
                shards_key = ShardKey(bs_hashes[i], ss_roots[i])
                shards_keys.append(Bytes(shards_key.encode()))

            # Erasure Root
            with benchmark("Calculated erasure root"):
                u = self.merkle.wb_merkle_fn(shards_keys)
            logger.info(f"Erasure Root calculated - {u.hex()} {u}")

            logger.info(f"Updating DA..")

            # Access DA
            d3l = settings.d3l
            audits = settings.audit_da

            # Store Exported Segments
            seg_da = SegmentsDA(d3l)
            with benchmark("Stored segments with proof"):
                seg_da.put(e, proved_segments)

            # Store Bundle Shards
            audits_da = AuditShardsDA(audits)
            with benchmark("Stored bundle shards"):
                audits_da.put_batch(u, bs_dict)

            # Store Segment Shards
            s_shards_da = SegmentShardsDA(d3l)
            with benchmark("Stored segment shards"):
                s_shards_da.put_batch(u, ss_dict)

            logger.info(f"Compiling availability specification..")

            with benchmark("Compiled spec"):
                spec = WorkPackageSpec(hash=package_hash, length=Uint[32](l), erasure_root=u, exports_root=e, exports_count=Uint[16](n))

            return spec
        except Exception as e:
            logger.error("Failed to build availability specification", error=e)
            raise

    def process_bundle(self, core: CoreIndex, bundle: WorkPackageBundle, sr_lookup: SegmentRootLookup) -> Tuple[WorkReport, WorkReportHash]:
        settings = self.settings
        try:
            # Generate Report
            logger.info("Building Work Report..")
            with benchmark("Report compiled"):
                report = self.build_report(bundle, core, sr_lookup)

            with open("work_report_single.txt", "a") as f:
                print(report, file=f)

            wr_hash = Hash.blake2b(report.encode())
            logger.info(f"Generated Work Report with hash {wr_hash}")

            # Access DA
            d3l = settings.d3l

            # Store Report
            reports_da = ReportsDA(d3l)
            reports_da.put(wr_hash, report)
            logger.info(f"Stored Work Report with hash {wr_hash}")

            return report, wr_hash

        except Exception as e:
            logger.error("Failed to process bundle", error=e)
            raise

    def process(self, package: WorkPackage, core: CoreIndex, extrinsics: Extrinsics):
        from jam.network.protocols.ce_134 import CoreSegment, WorkPackageSharing, CE134Data

        logger.info("Validating Work Package..")
        validator = Validator()
        validator.validate_wp(package)

        bundler = Bundler(self.node)

        # Build Segment Root Lookup Dictionary
        logger.info("Building Lookup Dictionary..")
        with benchmark("lookup built"):
            lookup = bundler.build_lookup(package)

        # Build Work Package Bundle
        logger.info("Building Work Package Bundle..")
        with benchmark("bundle built"):
            bundle = bundler.build_bundle(package, extrinsics)

        # Distribute Bundle to other Guarantors CE134
        CE134 = WorkPackageSharing()

        core_segment = CoreSegment(core_index=core, segment_root_map=lookup)

        map_len = U32(len(core_segment.encode()))
        bundle_len = U32(len(bundle.encode()))

        data = CE134Data(map_len=map_len, work_package_bundle=bundle, bundle_len=bundle_len, core_segment=core_segment)

        loop = asyncio.get_running_loop()
        loop.set_task_factory(asyncio.eager_task_factory)

        # Distribute Bundle, parallely
        self.transmit_task = loop.create_task(CE134.transmit(node=self.node, data=data))

        # Build Report
        with benchmark("bundle processed"):
            wr, wr_hash = self.process_bundle(core, bundle, lookup)

        with open("work_report.txt", "a") as f:
            print(wr, wr_hash, file=f)


        # Build Guarantee
        logger.info(f"Building guarantees..")
        with benchmark("guarantees signed"):
            try:
                # Wait for guarantees and process them
                asyncio.create_task(self.process_guarantees(wr, wr_hash))
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for async transmit result")
            except Exception as e:
                logger.error(f"Error waiting for async transmit result: {e}")

        return wr, wr_hash

    async def process_guarantees(self, wr: WorkReport, wr_hash: WorkReportHash):
        """
        Utility Async function for receiving guarantees and processing it.
        """
        settings = self.settings
        from jam.network.protocols.ce_135 import WorkReportDistribution, CE135Data

        ed25519_key = self.node.ed_pvt_key

        payload = wr.core_index.encode() + wr.encode()
        guarantee = b"jam_guarantee" + Hash.blake2b(payload).encode()

        # Sign the Guarantee
        sign = Ed25519Signature(ed25519_key.sign(guarantee))

        og_guarantee = ValidatorSignature(validator_index=ValidatorIndex(0), signature=sign)

        # Check majority & Build guarantees:
        guarantees = ValidatorSignatures([og_guarantee])

        # Working fix
        responses = await self.transmit_task
        logger.info("✅ Received responses: %s", responses)

        from jam.network.protocols.ce_134 import OptCred
        for response in responses:
            if response != OptCred(Null):
                cred = response.unwrap()
                if cred.work_report_hash == wr_hash:
                    guarantee = ValidatorSignature(validator_index=ValidatorIndex(0), signature=cred.ed25519_signature)
                    guarantees.append(guarantee)

        # Distribute Guaranteed WR to Validators CE135
        logger.info(f"Distributing Work Report to other validators..")
        if len(guarantees) > 1:

            d3l = settings.d3l

            map_da = PackageSegmentMap(d3l)
            sr_er_da = SegmentErasureMap(d3l)
            rep_da = ReportsDA(d3l)

            # Store Report
            rep_da.put(wr_hash, wr)

            # Store Segment Root - Erasure Root Mapping
            sr_er_da.put(root=wr.package_spec.exports_root, data=wr.package_spec.erasure_root)

            # Store Package Hash - Segment Root Mapping
            map_da.put(wr)

            # TODO: Save Assurers Mapping

            from jam.network.protocols.ce_135 import GuaranteedWR
            CE135 = WorkReportDistribution()
            # TODO: Fix timeslot
            gwr = GuaranteedWR(report=wr, slot=TimeSlot(0), signatures=guarantees)
            r_len = U32(len(gwr.encode()))
            data = CE135Data(len=r_len, guaranteed_wr=gwr)

            acks = await CE135.transmit(node=self.node, data=data)