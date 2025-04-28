from dataclasses import dataclass

from jam.types import decodable_vector, Vector
from jam.types.base.integers.fixed import U16, U8
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base.sequences.bytes.byte_array import ByteArray, decodable_bytearray
from jam.utils.byte_utils import ByteUtils
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.protocol.crypto import BandersnatchPublic, Ed25519Public, BlsPublic
from jam.utils.constants import VALIDATOR_COUNT
from jam.utils.json.serde import JsonSerde

@decodable_array(length=4, element_type=U8)
class IPAddress(Array): ...

@decodable_bytearray(122)
class ValidatorName(ByteArray): 
    def __init__(self, name: str):
        if isinstance(name, str):
            super().__init__(ByteUtils.to_bytes(name.encode("utf-8") + bytes(122 - len(name))))
        else:
            super().__init__(name)

    @staticmethod
    def from_json(json: str) -> "ValidatorName":
        return ValidatorName(json)

    # def __repr__(self) -> str:
        # return self.decode("utf-8")


@decodable_dataclass
@dataclass
class ValidatorMetadata(Codable, JsonSerde):
    """Validator metadata structure Byte-Array(128)"""
    # NOTE - Could define fns to parse metadata into a more useful format
    name: ValidatorName  # 122 Bytes
    host: IPAddress     # 4 Bytes
    port: U16           # 2 Bytes


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

@decodable_vector(element_type=ValidatorData)
class ValidatorVector(Vector[ValidatorData]):
    ...