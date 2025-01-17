from typing import Callable, Sequence, Type, Union, Any

from jam.types.base.bit import Bit, Bitable
from jam.types.base.boolean import Boolean
from jam.types.base.sequences.array import Array, decodable_array
from jam.utils.codec.composite.bit_sequences import BitSequenceCodec

class BitArray(Array[Bit]):
    """
    Fixed-length bit sequence implementation that supports codec operations.
    
    A BitSequence represents a fixed-length sequence of bits, where each bit
    is represented as a Boolean value. The sequence is encoded as a compact
    bit array.
    
    """
    
    length: int = 0
    
    def __init__(self, initial: Union[Sequence[Bitable], bytes, bytearray, memoryview, str]):
        """
        Initialize bit sequence.
        
        Args:
            length: Fixed length of the sequence in bits
            initial: Optional initial values. Must match the fixed length.
                    All elements must be Boolean instances.
                    
        Raises:
            TypeError: If elements are not Boolean instances
            ValueError: If initial values don't match fixed length
        """
        super().__init__(codec=BitSequenceCodec(self.length))
        
        # Format different types into a list of Booleans
        __data = []
        if isinstance(initial, bytearray) or isinstance(initial, bytes) or isinstance(initial, memoryview):
            __data = [Boolean(bool(bit)) for bit in initial]
        elif isinstance(initial, str):
            # TODO: Implement this
            # __data = [Boolean(bool(bit)) for bit in Byte(initial).to_bit_array("little")]
            # Take only the last length bits
            __data = __data[:self.length]
        elif isinstance(initial, Sequence):
            for item in initial:
                __data.append(Bit(item))
        
        
        if len(__data) != self.length:
            raise ValueError(f"Initial values must have length {self.length}")

        self._data = __data


def decodable_bit_sequence(length: int) -> Callable[[Type[Any]], Type[Any]]:
    """
    Extend existing decodable_array to be array of Bits
    """
    return decodable_array(length, Bit)