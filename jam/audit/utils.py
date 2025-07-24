from jam.ring_vrf.curve.specs.bandersnatch import (
    Bandersnatch_TE_Curve,
    BandersnatchPoint,
)
from jam.ring_vrf.ietf.ietf import IETF_VRF

from jam.utils import constants
from tsrkit_types import Bytes, TypedVector
from jam.utils.chainspec import chain_config
from jam.types.protocol.core import CoreIndex, ValidatorIndex
from jam.types.work.package import WorkPackage
from jam.types.work.manifest import Extrinsics
from jam.types.work.shard import ShardIndex
from jam.incore.bundler import Bundler
from jam.incore.validator import Validator

from jam.types.work.report import WorkReport, WorkReportHash
from jam.logging import get_logger


# Module-specific logger
logger = get_logger("in_core")

public_key = Bytes[32]


def sign_bandersnatch(key: Bytes[32], context: Bytes, message: bytes = b""):
    key = int.from_bytes(key)
    vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
    # Vrf2 = IETF_VRF(Ed25519_TE_Curve, Ed25519Point)
    output_point, proof = vrf.prove(
        alpha=message, secret_key=key, additional_data=context, salt=b""
    )
    op_bt_str = output_point.point_to_string()
    proof_bt_str = proof[0].to_bytes(32, "little") + proof[1].to_bytes(32, "little")
    signature = op_bt_str + proof_bt_str

    return signature


def audit_refine(package: WorkPackage, core: CoreIndex, extrinsics: Extrinsics):
    """This function for perform refine logic for specifically Auditing."""
    from jam.network.node import node
    from jam.incore.processor import Processor

    process = Processor(node=node)

    logger.debug("Validating work package..")
    validator = Validator()
    validator.validate_wp(package)

    bundler = Bundler(node)

    # Build Segment Root Lookup Dictionary
    logger.debug("Building lookup dictionary..")
    lookup = bundler.build_lookup(package)

    # Build Work Package Bundle
    logger.debug("Building work package bundle..")
    bundle = bundler.build_bundle(package, extrinsics)

    # Build Report
    logger.debug("Compiling report..")
    wr, wr_hash = process.process_bundle(core, bundle, lookup)

    return wr, wr_hash
