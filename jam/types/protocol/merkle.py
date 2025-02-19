from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.crypto import ByteArray32


# Merkle Mountain Range
@decodable_vector(element_type=ByteArray32)
class MMR(Vector[ByteArray32]):
    """Merkle Mountain Range"""

    ...
