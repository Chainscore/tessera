"""Core types for the JAM protocol."""
from dataclasses import dataclass
from typing import List, NewType, Tuple, Union

from jam.types.base.byte_array import ByteArray144
from .base import ByteArray32, U16, U32, U64
from .crypto import BandersnatchPublic, Ed25519Public, BlsPublic
from jam.utils.codec import (
    Codec, EncodeError, DecodeError,
    u8_codec, u16_codec, u32_codec, u64_codec,
    ArrayCodec, OptionCodec, VectorCodec, DictionaryCodec,
    BooleanCodec, StringCodec, BitSequenceCodec
)
from jam.utils.codec.composite.choices import ChoiceCodec
from jam.utils.codec.primitives.nulls import null_codec

# Core type aliases
OpaqueHash = NewType('OpaqueHash', ByteArray32)
TimeSlot = NewType('TimeSlot', U32)
ValidatorIndex = NewType('ValidatorIndex', U16)
CoreIndex = NewType('CoreIndex', U16)

# Hash type aliases
HeaderHash = NewType('HeaderHash', ByteArray32)
StateRoot = NewType('StateRoot', ByteArray32)
BeefyRoot = NewType('BeefyRoot', ByteArray32)
WorkPackageHash = NewType('WorkPackageHash', ByteArray32)
WorkReportHash = NewType('WorkReportHash', ByteArray32)
ExportsRoot = NewType('ExportsRoot', ByteArray32)
ErasureRoot = NewType('ErasureRoot', ByteArray32)

# Other core types
Gas = NewType('Gas', U64)
Entropy = NewType('Entropy', ByteArray32)

@dataclass
class ValidatorMetadata(Codec):
    """Validator metadata structure."""
    public_key: BlsPublic
    operator_address: Ed25519Public
    data_hash: OpaqueHash

    def encode_size(self) -> int:
        return (self.public_key.encode_size() +
                self.operator_address.encode_size() +
                self.data_hash.encode_size())

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        current_offset += ArrayCodec(144, u8_codec).encode_into(self.public_key, buffer, current_offset)
        current_offset += ArrayCodec(32, u8_codec).encode_into(self.operator_address, buffer, current_offset)
        current_offset += ArrayCodec(32, u8_codec).encode_into(self.data_hash, buffer, current_offset)
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple['ValidatorMetadata', int]:
        current_offset = offset
        public_key, size = BlsPublic.decode_from(buffer, current_offset)
        current_offset += size
        operator_address, size = Ed25519Public.decode_from(buffer, current_offset)
        current_offset += size
        data_hash, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        return ValidatorMetadata(public_key, operator_address, data_hash), current_offset - offset

@dataclass
class ValidatorData(Codec):
    """Validator data structure."""
    metadata: ValidatorMetadata
    stake: U64
    reputation: U32

    def encode_size(self) -> int:
        return (self.metadata.encode_size() +
                u64_codec.encode_size(self.stake) +
                u32_codec.encode_size(self.reputation))

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        current_offset += self.metadata.encode_into(buffer, current_offset)
        current_offset += u64_codec.encode_into(self.stake, buffer, current_offset)
        current_offset += u32_codec.encode_into(self.reputation, buffer, current_offset)
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple['ValidatorData', int]:
        current_offset = offset
        metadata, size = ValidatorMetadata.decode_from(buffer, current_offset)
        current_offset += size
        stake, size = u64_codec.decode_from(buffer, current_offset)
        current_offset += size
        reputation, size = u32_codec.decode_from(buffer, current_offset)
        current_offset += size
        return ValidatorData(metadata, stake, reputation), current_offset - offset

@dataclass
class EntropyBuffer(Codec):
    """Entropy buffer structure."""
    values: List[Entropy]

    def __post_init__(self):
        if len(self.values) != 4:
            raise ValueError("EntropyBuffer must contain exactly 4 entropy values")

    def encode_size(self) -> int:
        return VectorCodec(ArrayCodec(32, u8_codec)).encode_size(self.values)

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        return VectorCodec(ArrayCodec(32, u8_codec)).encode_into(self.values, buffer, offset)

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple['EntropyBuffer', int]:
        values, size = VectorCodec(ArrayCodec(32, u8_codec)).decode_from(buffer, offset)
        return EntropyBuffer(values), size

ServiceId = NewType('ServiceId', U32)

@dataclass
class ServiceInfo(Codec):
    """Service information structure."""
    code_hash: OpaqueHash
    balance: U64
    min_item_gas: Gas
    min_memo_gas: Gas
    bytes: U64
    items: U32

    def encode_size(self) -> int:
        return (ArrayCodec(32, u8_codec).encode_size(self.code_hash) +
                u64_codec.encode_size(self.balance) +
                u64_codec.encode_size(self.min_item_gas) +
                u64_codec.encode_size(self.min_memo_gas) +
                u64_codec.encode_size(self.bytes) +
                u32_codec.encode_size(self.items))

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        current_offset += ArrayCodec(32, u8_codec).encode_into(self.code_hash, buffer, current_offset)
        current_offset += u64_codec.encode_into(self.balance, buffer, current_offset)
        current_offset += u64_codec.encode_into(self.min_item_gas, buffer, current_offset)
        current_offset += u64_codec.encode_into(self.min_memo_gas, buffer, current_offset)
        current_offset += u64_codec.encode_into(self.bytes, buffer, current_offset)
        current_offset += u32_codec.encode_into(self.items, buffer, current_offset)
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple['ServiceInfo', int]:
        current_offset = offset
        code_hash, size = ArrayCodec(32, u8_codec).decode_from(buffer, current_offset)
        current_offset += size
        balance, size = u64_codec.decode_from(buffer, current_offset)
        current_offset += size
        min_item_gas, size = u64_codec.decode_from(buffer, current_offset)
        current_offset += size
        min_memo_gas, size = u64_codec.decode_from(buffer, current_offset)
        current_offset += size
        bytes, size = u64_codec.decode_from(buffer, current_offset)
        current_offset += size
        items, size = u32_codec.decode_from(buffer, current_offset)
        current_offset += size
        return ServiceInfo(code_hash, balance, min_item_gas, min_memo_gas, bytes, items), current_offset - offset