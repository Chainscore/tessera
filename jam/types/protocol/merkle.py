from jam.types.base.choices.option import Option, decodable_option
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.crypto import OpaqueHash

@decodable_option(OpaqueHash)
class OptionHash(Option): ...


@decodable_vector(OptionHash)
class MMR(Vector[OptionHash]): ...
