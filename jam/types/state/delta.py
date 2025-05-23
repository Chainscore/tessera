from dataclasses import dataclass, field
from typing import Dict, Type, Self, Sequence, Any, Union, Tuple

from jam.execution.utils import decode_code_hash
from jam.state.utils.key_constructor import construct_state_key
from jam.types.base import Byte
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.integers.fixed import U32, U64
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.base.sequences.bytes import ByteArray32, Bytes
from jam.types.protocol.core import Balance, BlobLength, Gas, ServiceId, TimeSlot
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde
from jam.types.protocol.crypto import Hash
from jam.utils.json.decorators import with_json_metadata


ServiceCodeHash = ByteArray32
# TODO - : Confirm these types + usage
"""Number of items in the account storage"""
Ai = U32

"""The total number of octets used in storage"""
Ao = U64

"""The minimum, or threshold, balance needed for any given service account"""
At = Balance

@with_json_metadata(
    code_hash   = { "name": "code_hash" },
    balance   = { "name": "balance"},
    gas_limit = { "name": "min_item_gas"},
    min_gas    = { "name": "min_memo_gas"},
    num_o    = { "name": "bytes"},
    num_i    = { "name": "items"},
)
@dataclass
@decodable_dataclass
class AccountMetadata(Codable, JsonSerde):
    code_hash: ServiceCodeHash  # code_hash
    balance: Balance  # balance
    gas_limit: Gas  # min_item_gas
    min_gas: Gas  # min_memo_gas
    num_o: Ao
    num_i: Ai

    @staticmethod
    def empty() -> "AccountMetadata":
        return AccountMetadata(
            code_hash=ByteArray32([0] * 32),
            balance=Balance(0),
            gas_limit=Gas(0),
            min_gas=Gas(0),
            num_i=Ai(0),
            num_o=Ao(0)
        )

@decodable_dictionary(ByteArray32, Bytes, key_name="key", value_name="value")
class AccountStorage(Dictionary[ByteArray32, Bytes]):
    """Storage dictionary"""
    _meta: AccountMetadata

    def __setitem__(self, key, value):
        if hasattr(self, "_meta"):
            is_new = key not in self.value
            if is_new:
                self._meta.num_i = self._meta.num_i + 1
                self._meta.num_o = self._meta.num_o + len(value) + 32
            else:
                self._meta.num_o = self._meta.num_o + len(value) - len(self.value[key])
        self.value[key] = value

    def __delitem__(self, key):
        exists = key in self.value
        if exists:
            self._meta.num_i = self._meta.num_i - 1
            self._meta.num_o = self._meta.num_o - len(self.value[key]) - 32
        del self.value[key]


@decodable_dictionary(ByteArray32, Bytes, key_name="hash", value_name="blob")
class AccountPreimages(Dictionary[ByteArray32, Bytes]):
    """Preimage dictionary"""
    ...

@decodable_vector(element_type=U32, max_length=3)
class Timestamps(Vector[U32]):
    """Lookup timestamps"""
    ...


@decodable_dataclass
@dataclass
class LookupTable(Codable, JsonSerde):
    hash: ByteArray32
    length: BlobLength

    def __hash__(self):
        return int(Hash.blake2b(self.length.encode() + self.hash.encode()))

    def to_json(self):
        return str(Hash.blake2b(self.length.encode() + self.hash.encode()))


@decodable_dictionary(LookupTable, Timestamps, key_name="key", value_name="value")
class AccountLookup(Dictionary[LookupTable, Timestamps]):
    """Lookup timestamps"""
    _meta: AccountMetadata

    def __setitem__(self, key: LookupTable, value):
        if hasattr(self, "_meta"):
            is_new = key not in self.value
            if is_new:
                self._meta.num_i = self._meta.num_i + 2
                self._meta.num_o = self._meta.num_o + key.length + 81
        self.value[key] = value

    def __delitem__(self, key: LookupTable):
        exists = key in self.value
        if exists:
            self._meta.num_i = self._meta.num_i - 1
            self._meta.num_o = self._meta.num_o - key.length - 81
        del self.value[key]


@with_json_metadata(
    # default in empty lists if JSON omits them
    service   = { "name": "service",    "default": AccountMetadata.empty() },
    storage   = { "name": "storage",    "default": AccountStorage({}) },
    preimages = { "name": "preimages",  "default": AccountPreimages({}) },
    lookup    = { "name": "lookup_meta",     "default": AccountLookup({}) },
)
@decodable_dataclass
@dataclass
class AccountData(Codable, JsonSerde):
    service: AccountMetadata
    storage: AccountStorage
    preimages: AccountPreimages
    lookup: AccountLookup

    def __post_init__(self):
        self.storage._meta = self.service
        self.lookup._meta = self.service

    def m_c(self) -> Union[Tuple[bytes, bytes], None]:
        img = self.preimages.get(self.service.code_hash)
        if img: return decode_code_hash(img)
        else: return None

    def historical_lookup(self, timeslot: TimeSlot, preimage_hash: ByteArray32):
        """
        https://graypaper.fluffylabs.dev/#/cc517d7/11c70011e000?v=0.6.5
        """
        if (
                self.preimages[preimage_hash] is not None and
                self.is_preimage_valid(
                    self.lookup[
                        LookupTable(hash=preimage_hash, length=BlobLength(len(self.lookup[preimage_hash])))],
                    timeslot
                )
        ):
            return self.preimages[preimage_hash]
        else:
            return None

    @classmethod
    def is_preimage_valid(cls, lookup_ts: Timestamps, current_ts: TimeSlot):
        """
        https://graypaper.fluffylabs.dev/#/cc517d7/11e700111201?v=0.6.5
        """
        if len(lookup_ts) == 0:
            return False
        elif len(lookup_ts) == 1:
            return lookup_ts[0] < current_ts
        elif len(lookup_ts) == 2:
            return lookup_ts[0] <= current_ts < lookup_ts[1]
        elif len(lookup_ts) == 3:
            return (lookup_ts[0] <= current_ts < lookup_ts[1]) or lookup_ts[2] <= ts
        else:
            raise ValueError("Invalid Timestamp data")


@decodable_dictionary(ServiceId, AccountData, key_name="id", value_name="data")
class Delta(Dictionary[ServiceId, AccountData]):
    """Delta state"""
    ...
