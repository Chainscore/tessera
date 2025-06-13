"""Epoch-related protocol types for the JAM protocol."""
from tsrkit_types.sequences import TypedArray
from tsrkit_types.struct import structure
from jam.types.protocol.crypto import BandersnatchPublic, Ed25519Public, Entropy
from jam.utils.constants import VALIDATOR_COUNT


@structure
class MinValidatorData:
    bandersnatch: BandersnatchPublic
    ed25519: Ed25519Public


ValidatorArray = TypedArray[MinValidatorData, VALIDATOR_COUNT]


@structure
class EpochMark:
    """Epoch mark structure."""

    entropy: Entropy
    tickets_entropy: Entropy
    validators: ValidatorArray
