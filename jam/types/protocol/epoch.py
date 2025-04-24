"""Epoch-related protocol types for the JAM protocol."""
from dataclasses import dataclass
from jam.types.base.sequences.array import Array, decodable_array
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.protocol.crypto import BandersnatchPublic, Ed25519Public, Entropy
from jam.utils.constants import VALIDATOR_COUNT
from jam.utils.json.serde import JsonSerde

@decodable_dataclass
@dataclass
class MinValidatorData(Codable, JsonSerde):
    bandersnatch: BandersnatchPublic
    ed25519: Ed25519Public

@decodable_array(length=VALIDATOR_COUNT, element_type=MinValidatorData)
class ValidatorArray(Array[MinValidatorData]):
    ...


@decodable_dataclass
@dataclass
class EpochMark(Codable, JsonSerde):
    """Epoch mark structure."""

    entropy: Entropy
    tickets_entropy: Entropy
    validators: ValidatorArray
