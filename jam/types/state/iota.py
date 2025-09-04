from tsrkit_types.sequences import TypedArray
from jam.types.protocol.validators import ValidatorData
from jam.utils.constants import VALIDATOR_COUNT


class Iota(TypedArray[ValidatorData, VALIDATOR_COUNT]):
    """
    Component: ι ∈ ⟦K⟧V , γP ∈ ⟦K⟧V , κ ∈ ⟦K⟧V , λ ∈ ⟦K⟧V
    Key: 7

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/0d7a010d7a01?v=0.7.0
    """
    ...
