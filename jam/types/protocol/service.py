from dataclasses import dataclass
from typing import List, Any, Tuple, Optional, Sequence, NewType, Union
from jam.types.base.integers import U32, U64
from jam.utils.codec.base import Codable
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import Gas

ServiceId = U32

@dataclass
class ServiceInfo(Codable):
    """Service information structure."""
    code_hash: OpaqueHash
    balance: U64
    min_item_gas: Gas
    min_memo_gas: Gas
    bytes_data: U64
    items: U32

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.code_hash, self.balance, self.min_item_gas,
                self.min_memo_gas, self.bytes_data, self.items]

    def encode_size(self) -> int:
        return sum(item.encode_size() for item in self.enc_sequence())

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        for item in self.enc_sequence():
            size = item.encode_into(buffer, current_offset)
            current_offset += size
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Any, int]:
        current_offset = offset
        decoded = []
        for item_type in [OpaqueHash, U64, Gas, Gas, U64, U32]:
            item, size = item_type.decode_from(buffer, current_offset)
            decoded.append(item)
            current_offset += size
        return ServiceInfo(*decoded), current_offset - offset 