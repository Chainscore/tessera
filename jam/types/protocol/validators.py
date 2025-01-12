from dataclasses import dataclass

from jam.types.base.sequences.array import Array, decodable_array
from jam.utils.codec import Codable, decodable_dataclass
from jam.types.protocol.crypto import (
    BandersnatchPublic, Ed25519Public, BlsPublic
)
from jam.utils.constants import VALIDATOR_COUNT

@decodable_array(length=VALIDATOR_COUNT, element_type=BandersnatchPublic)
class ValidatorArray(Array[BandersnatchPublic]): ...

@decodable_dataclass
@dataclass
class ValidatorMetadata(Codable):
    """Validator metadata structure."""
    data: bytes  # 128 bytes fixed size

@decodable_dataclass
@dataclass
class ValidatorData(Codable):
    """Validator data structure."""
    bandersnatch: BandersnatchPublic
    ed25519: Ed25519Public
    bls: BlsPublic
    metadata: ValidatorMetadata

"""Fixed-size array of validator data with size VALIDATOR_COUNT."""
@decodable_array(length=VALIDATOR_COUNT, element_type=ValidatorData)
class ValidatorsData(Array[ValidatorData]): ...
