from dataclasses import dataclass
from jam.types.base import BitSequence, decodable_bit_sequence
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.crypto import Ed25519Signature, OpaqueHash
from jam.types.protocol.core import ValidatorIndex
from jam.utils.codec import Codable, decodable_dataclass
from jam.utils.constants import CORE_COUNT

@decodable_bit_sequence(CORE_COUNT)
class AvailBitField(BitSequence): ...

@decodable_dataclass
@dataclass
class AvailAssurance(Codable):
    """Availability assurance structure."""
    anchor: OpaqueHash
    bitfield: AvailBitField
    validator_index: ValidatorIndex
    signature: Ed25519Signature

@decodable_vector(AvailAssurance)
class AssurancesExtrinsic(Vector[AvailAssurance]): ...