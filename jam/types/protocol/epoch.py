"""Epoch-related protocol types for the JAM protocol."""
from dataclasses import dataclass
from jam.types.protocol.validators import ValidatorArray
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.protocol.crypto import Entropy
from jam.utils.json.serde import JsonSerde

@decodable_dataclass
@dataclass
class EpochMark(Codable, JsonSerde):
    """Epoch mark structure."""
    entropy: Entropy
    tickets_entropy: Entropy
    validators: ValidatorArray