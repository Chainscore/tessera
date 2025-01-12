"""Epoch-related protocol types for the JAM protocol."""
from dataclasses import dataclass
from jam.types.protocol.validators import ValidatorArray
from jam.utils.codec import Codable, decodable_dataclass
from jam.types.protocol.crypto import Entropy

@decodable_dataclass
@dataclass
class EpochMark(Codable):
    """Epoch mark structure."""
    entropy: Entropy
    tickets_entropy: Entropy
    validators: ValidatorArray