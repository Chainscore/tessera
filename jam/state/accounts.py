from dataclasses import dataclass

from jam.execution.utils import decode_code_hash
from jam.storage.db.kv import KVStore
from jam.state.merkle import StateTrie
from jam.state.utils.key_constructor import construct_state_key
from jam.types.base import Bytes, ByteArray32, U32
from jam.types.protocol.core import Balance, Gas, ServiceId, TimeSlot, BlobLength
from jam.types.protocol.crypto import Hash
from jam.types.state.delta import AccountMetadata, ServiceCodeHash, Ao, Ai, LookupTable, Timestamps, AccountData
from jam.utils.constants import BASIC_MINIMUM_BALANCE, ADDITIONAL_BALANCE_PER_ITEM, ADDITIONAL_BALANCE_PER_OCTET


def make_account_prop(field):
    def getter(self):
        data = self.DB.get(bytes(construct_state_key((255, self.id))))
        if data is None:
            return None
        meta = AccountMetadata.decode_from(data)[0]
        return getattr(meta, field)
    def setter(self, value):
        data = self.DB.get(bytes(construct_state_key((255, self.id))))
        if data is None:
            return
        meta = AccountMetadata.decode_from(data)
        setattr(meta, field, value)
        k, v = construct_state_key((255, self.id)), meta.encode()  # Adjust encode as needed
        self.DB.put(bytes(k), v)
        self.TRIE.update(k, Bytes(v))
    return property(getter, setter)


class AccountDataView:
    def __init__(self, id: ServiceId, db: KVStore, trie: StateTrie):
        self.id = id
        self.DB = db
        self.TRIE = trie

    code_hash = make_account_prop('code_hash')
    balance = make_account_prop('balance')
    gas_limit = make_account_prop('gas_limit')  # min_item_gas
    min_gas = make_account_prop('min_gas')  # min_memo_gas
    num_o = make_account_prop('num_o')
    num_i = make_account_prop('num_i')

class Account:

    def __init__(self, id: ServiceId, db: KVStore, trie: StateTrie):
        self.id = id
        self.DB = db
        self.TRIE = trie

    @property
    def t(self):
        return Balance(BASIC_MINIMUM_BALANCE + ADDITIONAL_BALANCE_PER_ITEM * self.service.num_i + ADDITIONAL_BALANCE_PER_OCTET * self.service.num_o)

    @property
    def service(self):
        return AccountDataView(self.id, self.DB, self.TRIE)

    @service.setter
    def service(self, value: AccountMetadata):
        storage_key, encoded_val = bytes(construct_state_key((255, self.id))), value.encode()
        self.DB.put(storage_key, encoded_val)
        self.TRIE.update(Bytes(storage_key), Bytes(encoded_val))

    @property
    def storage(self):
        return StorageView(self.id, self.DB, self.TRIE)

    @property
    def preimages(self):
        return PreImageView(self.id, self.DB, self.TRIE)

    @property
    def lookup(self):
        return TimestampsView(self.id, self.DB, self.TRIE)

    def m_c(self) -> (bytes, bytes):
        return decode_code_hash(self.lookup[self.service.code_hash])

    def historical_lookup(self, timeslot: TimeSlot, preimage_hash: ByteArray32):
        """
            https://graypaper.fluffylabs.dev/#/cc517d7/11c70011e000?v=0.6.5
            """
        if (
                self.preimages[preimage_hash] is not None and
                self.is_preimage_valid(
                    self.lookup[
                        LookupTable(hash=preimage_hash, length=BlobLength(len(self.preimages[preimage_hash])))],
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

    def __repr__(self):
        return f"Account(id={self.id})"


class DeltaView:
    def __init__(self, db: KVStore, trie: StateTrie):
        self.DB = db
        self.TRIE = trie

    def __getitem__(self, key: ServiceId):
        return Account(
            id=key,
            db=self.DB,
            trie=self.TRIE,
        )

class StorageView:
    def __init__(self, id: ServiceId, db: KVStore, trie: StateTrie):
        self.id = id
        self.DB = db
        self.TRIE = trie

    def __getitem__(self, key: ByteArray32):
        data = self.DB.get(bytes(construct_state_key((self.id, Bytes(U32(2**32 - 1).encode()) + key[0:23]))))
        return Bytes(data) if data else data

    def __setitem__(self, key: ByteArray32, value: Bytes):
        k = construct_state_key((self.id, Bytes(U32(2 ** 32 - 1).encode()) + key[0:23]))
        # TODO - check for gas before adding, throw error if insufficient. This is supposed to be handled in relevent invocation
        self.DB.put(
            bytes(k),
            bytes(value)
        )
        self.TRIE.update(k, value)
        # TODO - update ai, ao

class PreImageView:
    def __init__(self, id: ServiceId, db: KVStore, trie: StateTrie):
        self.id = id
        self.DB = db
        self.TRIE = trie

    def __getitem__(self, key: ByteArray32):
        data = Bytes(U32(2**32 - 2).encode() + bytes(key)[1:24])
        data = self.DB.get(bytes(construct_state_key((self.id, data))))
        return Bytes(data) if data else data

    def __setitem__(self, key: ByteArray32, value: Bytes):
        k = construct_state_key((self.id, Bytes(U32(2 ** 32 - 2).encode()) + key[1:24]))
        self.DB.put(
            bytes(k),
            bytes(value)
        )
        self.TRIE.update(k, value)

class TimestampsView:
    def __init__(self, id: ServiceId, db: KVStore, trie: StateTrie):
        self.id = id
        self.DB = db
        self.TRIE = trie

    def __getitem__(self, key: LookupTable):
        data = self.DB.get(bytes(construct_state_key((self.id, Bytes(U32(key.length).encode()) + Hash.blake2b(bytes(key.hash))[2:25]))))
        return Timestamps.decode_from(data)[0] if data else data

    def __setitem__(self, key: LookupTable, value: Timestamps):
        k = construct_state_key((self.id, Bytes(U32(key.length).encode()) + Hash.blake2b(bytes(key.hash))[2:25]))
        v = value.encode()
        self.DB.put(bytes(k), bytes(v))
        self.TRIE.update(k, Bytes(value))
