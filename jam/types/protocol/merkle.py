from tsrkit_types.option import Option
from tsrkit_types.sequences import TypedVector
from jam.types.protocol.crypto import OpaqueHash


class OptionHash(Option[OpaqueHash]):
    def __hash__(self):
        value = self.unwrap()
        return int.from_bytes(bytes(value))


class MMR(TypedVector[OptionHash]):
    ...
