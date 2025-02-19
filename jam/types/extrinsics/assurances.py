from dataclasses import dataclass
from jam.types.base import BitArray, decodable_bit_array
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.crypto import Ed25519Signature, OpaqueHash
from jam.types.protocol.core import ValidatorIndex
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.constants import CORE_COUNT
from jam.utils.json.serde import JsonSerde


@decodable_bit_array(length=CORE_COUNT, bitorder="lsb")
class AvailBitField(BitArray):
    ...


@decodable_dataclass
@dataclass
class AvailAssurance(Codable, JsonSerde):
    """Availability assurance structure."""

    anchor: OpaqueHash
    bitfield: AvailBitField
    validator_index: ValidatorIndex
    signature: Ed25519Signature


@decodable_vector(AvailAssurance)
class AssurancesExtrinsic(Vector[AvailAssurance]):
    ...
