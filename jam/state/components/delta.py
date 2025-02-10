from dataclasses import dataclass
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.integers.fixed import U32, U64
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base.sequences.bytes import ByteArray32, Bytes
from jam.types.protocol.core import Balance, BlobLength, Gas, ServiceId
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass

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

@decodable_array(length=3, element_type=U32)
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

#TODO - : Confirm these types + usage
"""Number of items in the account storage"""
Ai = U32

"""The total number of octets used in storage"""
Ao = U64

"""The minimum, or threshold, balance needed for any given service account"""
At = Balance