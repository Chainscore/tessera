from jam.types.base.choices.option import Option, decodable_option
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.crypto import OpaqueHash

@decodable_option(OpaqueHash)
class OptionHash(Option):
	def __hash__(self):
		value = self.get_value()
		return int.from_bytes(bytes(value))


@decodable_vector(OptionHash)
class MMR(Vector[OptionHash]): ...
