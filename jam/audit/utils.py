from typing import Optional

from jam.ring_vrf.curve.specs.bandersnatch import Bandersnatch_TE_Curve, BandersnatchPoint
from jam.ring_vrf.ietf.ietf import IETF_VRF

from jam.utils import constants
from tsrkit_types import Bytes, TypedVector
from jam.utils.chainspec import chain_config
from jam.types.protocol.core import CoreIndex, ValidatorIndex
from jam.types.work.package import WorkPackage
from jam.types.work.manifest import Extrinsics
from jam.types.work.shard import  ShardIndex
from jam.work_package.bundler import Bundler
from jam.work_package.validator import Validator
from jam.logging import get_logger


# Module-specific logger
logger = get_logger("in_core")

public_key = Bytes[32]

def sign_bandersnatch(key: Bytes[32], context: Bytes, message:bytes=b"") :

    key = int.from_bytes(key)
    vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
    # Vrf2 = IETF_VRF(Ed25519_TE_Curve, Ed25519Point)
    output_point, proof = vrf.prove(alpha=message, secret_key=key,  additional_data=context, salt=b"")
    op_bt_str= output_point.point_to_string()
    proof_bt_str= proof[0].to_bytes(32, 'little')+ proof[1].to_bytes(32, 'little')
    signature= op_bt_str + proof_bt_str
    return signature



# vi = (si - CI * t) % validators
def get_vi(shard_index: ShardIndex, core_index: CoreIndex):

    validator_index = ValidatorIndex(
        (shard_index - core_index * chain_config.recovery_threshold)
        % constants.VALIDATOR_COUNT
    )

    return validator_index

# si = (CI * t + vi) % validators
def get_si(validator_index: ValidatorIndex, core_index: CoreIndex):

    shard_index = ShardIndex(
        (core_index * chain_config.recovery_threshold + validator_index)
        % constants.VALIDATOR_COUNT
    )

    return shard_index


def audit_refine(self, package: WorkPackage, core: CoreIndex, extrinsics: Extrinsics):
    from jam.network.protocols.ce_134 import CoreSegment, WorkPackageSharing, CE134Data

    logger.debug("Validating work package..")
    validator = Validator()
    validator.validate_wp(package)

    bundler = Bundler(self.node)

    # Build Segment Root Lookup Dictionary
    logger.debug("Building lookup dictionary..")
    lookup = bundler.build_lookup(package)

    # Build Work Package Bundle
    logger.debug("Building work package bundle..")
    bundle = bundler.build_bundle(package, extrinsics)

    # Build Report
    logger.debug("Compiling report..")
    wr, wr_hash = self.process_bundle(core, bundle, lookup)

    return wr, wr_hash