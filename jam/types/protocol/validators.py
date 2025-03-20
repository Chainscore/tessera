from dataclasses import dataclass

from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.base.sequences.bytes.byte_array import ByteArray128
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.protocol.crypto import BandersnatchPublic, Ed25519Public, BlsPublic
from jam.utils.constants import VALIDATOR_COUNT
from jam.utils.json.serde import JsonSerde


@decodable_array(length=VALIDATOR_COUNT, element_type=BandersnatchPublic)
class ValidatorArray(Array[BandersnatchPublic]):
    ...


class ValidatorMetadata(ByteArray128):
    """Validator metadata structure."""

    # NOTE - Could define fns to parse metadata into a more useful format
    ...


@decodable_dataclass
@dataclass
class ValidatorData(Codable, JsonSerde):
    """Validator data structure."""

    bandersnatch: BandersnatchPublic
    ed25519: Ed25519Public
    bls: BlsPublic
    metadata: ValidatorMetadata


"""Fixed-size array of validator data with size VALIDATOR_COUNT."""


@decodable_array(length=VALIDATOR_COUNT, element_type=ValidatorData)
class ValidatorsData(Array[ValidatorData]):
    ...


@decodable_vector(ValidatorData)
class ValidatorsVector(Vector[ValidatorData]):
    ...
