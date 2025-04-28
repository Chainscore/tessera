from dataclasses import dataclass
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.integers.fixed import U32, U64
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.base.sequences.bytes import ByteArray32, Bytes
from jam.types.protocol.core import Balance, BlobLength, Gas, ServiceId
from jam.types.protocol.crypto import Hash
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde
from jam.types.protocol.crypto import Hash
from jam.state.components.phi import Phi
from jam.state.components.chi import Chi

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
class LookupTable(Codable, JsonSerde):
    hash: ByteArray32
    length: BlobLength

    def __hash__(self) -> int:
        return int.from_bytes(bytes(Hash.sha256(bytes(self.hash) + bytes(self.length))))

@decodable_vector(element_type=U32, max_length=3)
class Timestamps(Vector[U32]):
    """Lookup timestamps"""
    ...

@decodable_dictionary(LookupTable, Timestamps)
class LookupTimestamps(Dictionary[LookupTable, Timestamps]):
    """Lookup timestamps"""

    @staticmethod
    def get_key(hash: ByteArray32, length: BlobLength) -> ByteArray32:
        return ByteArray32(Bytes(length.encode()) + Hash.blake2b(hash)[2:26] + Bytes(bytearray(4)))

    @staticmethod
    def get_length(hash: ByteArray32) -> BlobLength:
        return BlobLength(int.from_bytes(bytes(Bytes(hash[0:4])), byteorder='little'))
    ...


@decodable_dataclass
@dataclass
class AccountData(Codable, JsonSerde):
    storage: AccountStorage  
    lookup: PreImageLookup # preimages
    timestamps: LookupTimestamps 
    code_hash: ServiceCodeHash # code_hash
    balance: Balance # balance
    gas_limit: Gas # min_item_gas
    min_gas: Gas # min_memo_gas


@decodable_dictionary(ServiceId, AccountData)
class Delta(Dictionary[ServiceId, AccountData]):
    """Delta state"""

    ...


# TODO - : Confirm these types + usage
"""Number of items in the account storage"""
Ai = U32

"""The total number of octets used in storage"""
Ao = U64

"""The minimum, or threshold, balance needed for any given service account"""
At = Balance
