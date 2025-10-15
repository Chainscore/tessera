import asyncio

from tsrkit_types import U32, Bytes, Vector

from jam.audit.error import AssemblerError, AssemblerErrorCode as Code
from jam.network.utils.shards import get_si, get_vi
from jam.settings import Settings

from jam.storage.da.audits import AuditShardsDA

from jam.types.protocol.core import SegmentRoot
from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.types.work.item import ExtrinsicSpecs, ImportSpecs
from jam.types.work.manifest import (
    Assurers,
    Extrinsics,
    Segments,
    Justifications,
    SegmentRootLookup,
)
from jam.types.work.package import WorkPackageBundle
from jam.types.work.report import WorkReport
from jam.types.work.shard import ShardKey, ShardIndex, SegmentsShardRoot

from jam.utils.chainspec import chain_config
from jam.utils.constants import VALIDATOR_COUNT
from jam.utils.merkle import BMRFunctions
from jam.utils.erasure_coding.erasure_code import ErasureCode
from jam.utils.merkle.binary_merkle import OpaqueHashes
from jam.log_setup import node_logger as logger


class Assembler:
    # node: Node
    merklizer: BMRFunctions
    codec: ErasureCode
    settings: Settings

    def __init__(self):
        from jam.settings import settings

        self.codec = ErasureCode()
        self.merklizer = BMRFunctions()
        self.settings = settings

    async def assemble_bundle(self, wr: WorkReport):
        from jam.network.protocols.ce_137 import Query
        from jam.network.protocols.ce_138 import AuditShardRequestProtocol, CE138Data

        CE138 = AuditShardRequestProtocol()

        er_root = wr.package_spec.erasure_root
        wr_hash = wr.hash()

        # Fetch shard info of current node
        v_i = self.settings.validator_index
        s_i = get_si(validator_index=v_i, core_index=wr.core_index)

        # Fetch shards from other nodes
        total_shards = VALIDATOR_COUNT

        shards = Vector([])
        for i in range(total_shards):
            if len(shards) > chain_config.recovery_threshold:
                logger.info("Collected all shards", cnt=len(shards))
                break

            try:
                if i == s_i:
                    bs_da = AuditShardsDA(self.settings.audit_da)
                    bs_dict = bs_da.get(er_root)

                    if bs_dict and s_i in bs_dict:
                        shards.append((bs_dict[s_i], s_i))

                else:
                    assurer_vi = get_vi(shard_index=i, core_index=wr.core_index)
                    query = Query(er_root, ShardIndex(i))
                    data = CE138Data(U32(len(query.encode())), query)

                    # responses = await CE138.transmit(self.node, data, Assurers([assurer_vi]))
                    try:
                        responses = await asyncio.wait_for(
                            CE138.transmit(data, Assurers([assurer_vi])), timeout=2
                        )
                    except asyncio.TimeoutError:
                        logger.warning(
                            "Timeout while waiting for shard response.",
                            index=i,
                            er_root=er_root.hex()[:16] + "...",
                        )
                        continue

                    # Verify Shard
                    if not responses or len(responses) != 1:
                        raise AssemblerError(
                            Code.INVALID_RESPONSE, "Didn't receive shard from expected assurer."
                        )
                    response = responses[0]

                    jfn = response[1]
                    bs = response[0]
                    bs_hash = Hash.blake2b(bs.encode())
                    # shards.append((bs, i))

                    leaf = Bytes(ShardKey(bs_hash, SegmentsShardRoot(jfn[-1])).encode())
                    trace = jfn[:-1]
                    merklizer = BMRFunctions()

                    is_correct = merklizer.verify_wb_tree(leaf, er_root, i, trace)
                    if is_correct:
                        shards.append((bs, i))
                    else:
                        raise AssemblerError(
                            Code.INCORRECT_SHARD, "Couldn't verify received shard."
                        )

            except Exception as SHARD_MISS:
                logger.error(
                    "Failed to fetch audit shard.",
                    err=str(SHARD_MISS),
                    err_type=type(SHARD_MISS).__name__,
                    er_root=er_root.hex()[:16] + "...",
                    index=i,
                )

        if len(shards) < chain_config.recovery_threshold:
            logger.error(
                "Couldn't fetch minimum required audit shards",
                er_root=er_root.hex()[:16] + "...",
                wr_hash=wr_hash.hex()[:16] + "...",
                collected=len(shards),
            )

            raise AssemblerError(Code.SHARDS_UNAVAILABLE)

        bundle = self.codec.decode(shards)
        bundle = WorkPackageBundle.decode(bundle)

        return bundle

    @staticmethod
    def _lookup_root(r: OpaqueHash, sr_lookup: SegmentRootLookup) -> SegmentRoot:
        if sr_lookup is not None and r in sr_lookup.keys():
            return sr_lookup[r]
        else:
            return r

    def validate_bundle(self, wr: WorkReport, bundle: WorkPackageBundle):
        from jam.incore import Validator

        validator = Validator()

        wp = bundle.package
        segs = bundle.import_segments
        jfns = bundle.justifications
        ext = bundle.extrinsics

        spec = wr.package_spec

        # First Validate Work Package
        wp_hash = Hash.blake2b(wp.encode())
        if wp_hash != spec.hash:
            raise AssemblerError(Code.FAULTY_BUNDLE, "Work Package Hash mismatch")

        # Validate Package Constraints
        is_valid = validator.validate_wp(wp)
        if not is_valid:
            raise AssemblerError(Code.FAULTY_BUNDLE, "Invalid Work Package")

        # Then validate extrinsics
        if len(wp.items) != len(ext):
            raise AssemblerError(Code.FAULTY_BUNDLE, "Extrinsics not sufficient for all work items")

        for i, item in enumerate(wp.items):
            ext_specs: ExtrinsicSpecs = item.extrinsic
            ext_i: Extrinsics = ext[i]

            if len(ext_specs) != len(ext_i):
                raise AssemblerError(
                    Code.FAULTY_BUNDLE, f"Extrinsics not sufficient for work item {i}"
                )

            for j, (ext_spec, data) in enumerate(zip(ext_specs, ext_i)):
                ext_hash = Hash.blake2b(data.encode())

                if ext_spec.hash != ext_hash or ext_spec.len != len(data):
                    raise AssemblerError(
                        Code.FAULTY_BUNDLE, f"Invalid Extrinsic {j} for work item {i}"
                    )

        # Validate Segments
        if len(wp.items) != len(jfns):
            raise AssemblerError(
                Code.FAULTY_BUNDLE, "Justifications not sufficient for all work items"
            )

        if len(wp.items) != len(segs):
            raise AssemblerError(Code.FAULTY_BUNDLE, "Segments not sufficient for all work items")

        for i, item in enumerate(wp.items):
            imp_specs: ImportSpecs = item.import_segments
            imp_i: Segments = ext[i]
            jfn_i: Justifications = jfns[i]

            if len(imp_specs) != len(imp_i):
                raise AssemblerError(
                    Code.FAULTY_BUNDLE, f"Segments not sufficient for work item {i}"
                )

            if len(imp_specs) != len(jfn_i):
                raise AssemblerError(
                    Code.FAULTY_BUNDLE, f"Justifications not sufficient for work item {i}"
                )

            for j, (imp_spec, seg, jfn) in enumerate(zip(imp_specs, imp_i, jfn_i)):
                leaf = Hash.blake2b(Bytes(b"leaf") + Bytes(seg))

                exp_root = self._lookup_root(imp_spec.tree_root, wr.segment_root_lookup)
                root = self.merklizer.verify_cd_tree(jfn, OpaqueHashes([leaf]), imp_spec.index)

                if exp_root != root:
                    raise AssemblerError(
                        Code.FAULTY_BUNDLE,
                        f"Invalid Segment / Justification, {j} for work item {i}",
                    )

    async def assemble(self, wr: WorkReport):
        wr_hash = wr.hash()

        try:
            bundle = await self.assemble_bundle(wr)

            self.validate_bundle(wr, bundle)

            logger.info("🔨🪛 Assembled Bundle..", wr_hash=wr_hash.hex())
            return bundle

        except Exception as BUNDLE_MISS:
            logger.error(
                "Error occurred while assembling work package bundle.",
                wr_hash=wr_hash.hex(),
                err=str(BUNDLE_MISS),
                err_type=type(BUNDLE_MISS).__name__,
            )
