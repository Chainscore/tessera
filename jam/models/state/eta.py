from tsrkit_types.sequences import TypedArray
from jam.models.protocol.crypto import OpaqueHash

"""Fixed-size array of entropy values with size 4."""

class Eta(TypedArray[OpaqueHash, 4]):
    """
    Component: η
    Key: 6

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/0eb3020ebb02?v=0.7.0
    """

    ...
