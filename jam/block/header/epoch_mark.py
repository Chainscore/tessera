from jam.models.state.sigma import Sigma
from tsrkit_types import structure, Option, TypedArray, Null, U64
from typing import Self
from jam.models.protocol.crypto import Entropy
from jam.utils.constants import EPOCH_LENGTH
from jam.models.protocol.crypto import BandersnatchPublic, Ed25519Public, Entropy
from jam.utils.constants import VALIDATOR_COUNT


@structure
class MinValidatorData:
    bandersnatch: BandersnatchPublic
    ed25519: Ed25519Public


class ValidatorArray(TypedArray[MinValidatorData, VALIDATOR_COUNT]):
    ...


@structure
class EpochMarkData:
    """Epoch mark structure."""

    entropy: Entropy
    tickets_entropy: Entropy
    validators: ValidatorArray


class EpochMark(Option[EpochMarkData]):
    @classmethod
    def produce(cls, state: Sigma, slot: U64) -> Self:
        """
        Returns the epoch marker for the given state
        https://graypaper.fluffylabs.dev/#/68eaa1f/0e3d030e3e03?v=0.6.4
        - Ensure we are moving to a new epoch
        """
        if slot // EPOCH_LENGTH > state.tau // EPOCH_LENGTH:
            return cls(
                EpochMarkData(
                    entropy=Entropy(state.eta[0]),
                    tickets_entropy=Entropy(state.eta[1]),
                    validators=ValidatorArray(
                        [
                            MinValidatorData(bandersnatch=val.bandersnatch, ed25519=val.ed25519)
                            for val in state.gamma.p
                        ]
                    ),
                )
            )
        else:
            return cls(Null)
