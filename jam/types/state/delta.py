from dataclasses import field
from typing import Self
from tsrkit_types import Bytes
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.integers import Uint, U32
from tsrkit_types.sequences import TypedBoundedVector
from tsrkit_types.struct import structure
from jam.state.utils import construct_state_key
from jam.types.protocol.core import Balance, BlobLength, Gas, ServiceId, TimeSlot
from jam.types.protocol.crypto import Hash
from jam.utils.constants import (
    BASIC_MINIMUM_BALANCE,
    ADDITIONAL_BALANCE_PER_ITEM,
    ADDITIONAL_BALANCE_PER_OCTET,
)


ServiceCodeHash = Bytes[32]
"""Number of items in the account storage"""
Ai = Uint[32]

"""The total number of octets used in storage"""
Ao = Uint[64]

"""The minimum, or threshold, balance needed for any given service account"""
At = Balance


@structure
class AccountMetadata:
    code_hash: ServiceCodeHash  # code_hash, c
    balance: Balance  # balance, b
    gas_limit: Gas = field(metadata={"name": "min_item_gas"}) # g
    min_gas: Gas = field(metadata={"name": "min_memo_gas"}) # m
    num_o: Ao = field(metadata={"name": "bytes"}) # o
    gratis_offset: Balance = field(metadata={"name": "deposit_offset"}) # f
    num_i: Ai = field(metadata={"name": "items"}) # i
    created_at: TimeSlot = field(metadata={"name": "creation_slot"}) # r
    accumulated_at: TimeSlot = field(metadata={"name": "last_accumulation_slot"}) # a
    parent_service: ServiceId # p

    @property
    def t(self):
        return max(Balance(0), Balance(
            BASIC_MINIMUM_BALANCE
            + ADDITIONAL_BALANCE_PER_ITEM * self.num_i
            + ADDITIONAL_BALANCE_PER_OCTET * self.num_o
            - self.gratis_offset
        ))

    @staticmethod
    def empty() -> "AccountMetadata":
        return AccountMetadata(
            code_hash=Bytes[32](32),
            balance=Balance(0),
            gratis_offset=Balance(0),
            gas_limit=Gas(0),
            min_gas=Gas(0),
            created_at=TimeSlot(0),
            accumulated_at=TimeSlot(0),
            parent_service=ServiceId(1),
            num_i=Ai(0),
            num_o=Ao(0),
        )


class AccountStorage(Dictionary[Bytes, Bytes, "key", "value"]):
    """Storage dictionary"""

    _meta: AccountMetadata

    def __setitem__(self, key, value):
        if hasattr(self, "_meta"):
            is_new = key not in self
            if is_new:
                self._meta.num_i = Ai(self._meta.num_i + 1)
                self._meta.num_o = Ao(self._meta.num_o + len(value) + 34 + len(key))
            else:
                diff = len(value) - len(self[key])
                self._meta.num_o = Ao(self._meta.num_o + diff)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        exists = key in self
        if exists:
            self._meta.num_i = Ai(self._meta.num_i - 1)
            self._meta.num_o = Ao(self._meta.num_o - len(self[key]) - 34 - len(key))
        super().__delitem__(key)
        
    def transform(self, service_id: ServiceId):
        res = {}
        for k, v in self.items():
            res[construct_state_key((service_id, Bytes(U32(2**32 - 1).encode()) + k))] = v
        return res


"""Preimage dictionary"""
class AccountPreimages(Dictionary[Bytes[32], Bytes, "hash", "blob"]):
    
    def transform(self, service_id: ServiceId):
        res = {}
        for k, v in self.items():
            res[construct_state_key((service_id, Bytes(U32(2**32 - 2).encode()) + k))] = v
        return res


"""Lookup timestamps"""
Timestamps = TypedBoundedVector[U32, 0, 3]


@structure
class LookupTable:
    hash: Bytes[32]
    length: BlobLength

    def __hash__(self):
        return int.from_bytes(Hash.blake2b(self.length.encode() + self.hash.encode()))

    def to_json(self):
        return self.encode().hex()

    @classmethod
    def from_json(cls, data: dict | str) -> Self:
        if isinstance(data, dict):
            return cls(Bytes[32].from_json(data["hash"]), BlobLength(data["length"]))
        return cls.decode(bytes.fromhex(data))

class AccountLookup(Dictionary[LookupTable, Timestamps, "key", "value"]):
    """Lookup timestamps"""

    _meta: AccountMetadata

    def __setitem__(self, key: LookupTable, value):
        if hasattr(self, "_meta"):
            is_new = key not in self
            if is_new:
                self._meta.num_i = Ai(self._meta.num_i + 2)
                self._meta.num_o = Ao(self._meta.num_o + key.length + 81)
        super().__setitem__(key, value)

    def __delitem__(self, key: LookupTable):
        if key in self:
            self._meta.num_i = Ai(self._meta.num_i - 2)
            self._meta.num_o = Ao(self._meta.num_o - key.length - 81)
        super().__delitem__(key)

    def transform(self, service_id: ServiceId):
        res = {}
        for k, v in self.items():
            res[construct_state_key((service_id, Bytes(U32(k.length).encode()) + k.hash))] = v.encode()
        return res

@structure
class AccountData:
    """
    Set A
    Account Data Structure.

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/10510110a401?v=0.7.0
    """

    service: AccountMetadata = field(metadata={"default": AccountMetadata.empty()})
    storage: AccountStorage = field(metadata={"default": AccountStorage({})})
    preimages: AccountPreimages = field(metadata={"default": AccountPreimages({})})
    lookup: AccountLookup = field(metadata={"name": "lookup_meta", "default": AccountLookup({})})

    def __post_init__(self):
        self.storage._meta = self.service
        self.lookup._meta = self.service
        
    def transform(self, service_id: ServiceId):
        res = {}
        res[construct_state_key((255, service_id))] = self.service.encode()
        res.update(self.storage.transform(service_id))
        res.update(self.preimages.transform(service_id))
        res.update(self.lookup.transform(service_id))
        return res


class Delta(Dictionary[ServiceId, AccountData, "id", "data"]):
    """
    Component: δ
    Key: Variable Keys

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/102601102601?v=0.7.0
    """

    def transform(self) -> dict:
        res = {}
        for sid, account in self.items():
            res.update(account.transform(sid))
        return res