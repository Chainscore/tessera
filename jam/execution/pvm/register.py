from typing import Self
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.protocol.core import Register
from jam.utils.constants import PVM_INIT_DATA_SIZE, PVM_INIT_ZONE_SIZE, REGISTER_COUNT


@decodable_array(element_type=Register, length=REGISTER_COUNT)
class Registers(Array):

    @classmethod
    def from_pc(cls, args) -> Self:
        result = cls([Register(0)] * 13)
        result[0] = Register(2**32 - 2**16)
        result[1] = Register(2**32 - 2*PVM_INIT_ZONE_SIZE - PVM_INIT_DATA_SIZE)
        result[7] = Register(2**32 - PVM_INIT_ZONE_SIZE - PVM_INIT_DATA_SIZE)
        result[8] = Register(len(args))
        return result