from tsrkit_types.option import Option
from tsrkit_types.sequences import TypedVector
from jam.types.protocol.crypto import OpaqueHash


class OptionHash(Option[OpaqueHash]):
	def __hash__(self):
		value = self.get_value()
		return int.from_bytes(bytes(value))


MMR = TypedVector[OptionHash]
