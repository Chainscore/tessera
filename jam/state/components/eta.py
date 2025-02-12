from jam.types.base.sequences.array import Array, decodable_array
from jam.types.protocol.crypto import OpaqueHash

"""Fixed-size array of entropy values with size 4."""
@decodable_array(length=4, element_type=OpaqueHash)
class Eta(Array[OpaqueHash]):
    """Entropy buffer"""
    ...