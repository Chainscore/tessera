from tsrkit_types.bits import Bits
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure

from jam.types.protocol.crypto import Ed25519Signature, OpaqueHash
from jam.types.protocol.core import ValidatorIndex
from jam.utils.constants import CORE_COUNT


AvailBitField = Bits[CORE_COUNT, "lsb"]


@structure
class AvailAssurance:
    """Availability assurance structure."""

    anchor: OpaqueHash
    bitfield: AvailBitField
    validator_index: ValidatorIndex
    signature: Ed25519Signature


AssurancesExtrinsic = TypedVector[AvailAssurance]


@structure
class AvailAssuranceNetwork:
    """Availability assurance structure."""
    anchor: OpaqueHash
    bitfield: AvailBitField
    signature: Ed25519Signature

AssurancesExtrinsic_network = TypedVector[AvailAssuranceNetwork]
