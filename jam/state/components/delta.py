
from dataclasses import dataclass
from multiprocessing.dummy import Array
from jam.types.base.bytes import Bytes
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.array import decodable_array
from jam.types.base.sequences.byte_array import ByteArray32
from jam.types.protocol.core import Balance, BlobLength, Gas, ServiceId
from jam.utils.codec.base import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass

ServiceCodeHash = ByteArray32

@decodable_dictionary(ByteArray32, Bytes)
class AccountStorage(Dictionary[ByteArray32, Bytes]):
    """Storage dictionary"""
    ...

@decodable_dictionary(ByteArray32, Bytes)
class PreImageLookup(Dictionary[ByteArray32, Bytes]):
    """Lookup dictionary"""
    ...

@decodable_dataclass
@dataclass
class LookupTable(Codable):
    data: ByteArray32
    length: BlobLength

@decodable_array(3, U32)
class Timestamps(Array[U32]):
    """Lookup timestamps"""
    ...

@decodable_dictionary(ByteArray32, Timestamps)
class LookupTimestamps(Dictionary[ByteArray32, Timestamps]):
    """Lookup timestamps"""
    ...

@decodable_dataclass
@dataclass
class AccountData(Codable):
    storage: AccountStorage
    lookup: PreImageLookup
    timestamps: LookupTimestamps
    code_hash: ServiceCodeHash
    balance: Balance
    gas_limit: Gas
    min_gas: Gas

@decodable_dictionary(ServiceId, AccountData)
class Delta(Dictionary[ServiceId, AccountData]):
    """Delta state"""
    ...
