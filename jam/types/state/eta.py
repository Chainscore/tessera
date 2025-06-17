from tsrkit_types.sequences import TypedArray
from jam.types.protocol.crypto import OpaqueHash

"""Fixed-size array of entropy values with size 4."""

Eta = TypedArray[OpaqueHash, 4]
