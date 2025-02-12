from jam.types.base.sequences.array import Array, decodable_array
from jam.types.protocol.core import Register
from jam.utils.constants import REGISTER_COUNT


@decodable_array(element_type=Register, length=REGISTER_COUNT)
class Registers(Array):
    ...
