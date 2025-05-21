from dataclasses import dataclass

from jam.execution.utils import decode_code_hash
from jam.storage.db.kv import KVStore
from jam.state.merkle import StateTrie
from jam.state.utils.key_constructor import construct_state_key
from jam.types.base import Bytes, ByteArray32, U32
from jam.types.protocol.core import Balance, Gas, ServiceId, TimeSlot, BlobLength
from jam.types.protocol.crypto import Hash
from jam.types.state.delta import AccountMetadata, ServiceCodeHash, Ao, Ai, LookupTable, Timestamps
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.utils.codec.primitives.bytes import BytesCodec
from jam.utils.json import JsonSerde
from jam.utils.constants import BASIC_MINIMUM_BALANCE, ADDITIONAL_BALANCE_PER_ITEM, ADDITIONAL_BALANCE_PER_OCTET





class Account:
    def __init__(self, id: ServiceId, db: KVStore, trie: StateTrie, data: AccountMetadata):
        self.id = id
        self.DB = db
        self.TRIE = trie
        self.data = data

    @property
    def code_hash(self):    return self.data.code_hash
    @code_hash.setter
    def code_hash(self, value):
        self.data.code_hash = value
        k, v = construct_state_key((255, self.id)), self.data.encode()
        self.DB.put(bytes(k), v)
        self.TRIE.update(k, Bytes(v))

    @property
    def balance(self):      return self.data.balance
    @balance.setter
    def balance(self, value):
        self.data.balance = value
        k, v = construct_state_key((255, self.id)), self.data.encode()
        self.DB.put(bytes(k), v)
        self.TRIE.update(k, Bytes(v))

    @property
    def gas_limit(self):    return self.data.gas_limit
    @gas_limit.setter
    def gas_limit(self, value):
        self.data.gas_limit = value
        k, v = construct_state_key((255, self.id)), self.data.encode()
        self.DB.put(bytes(k), v)
        self.TRIE.update(k, Bytes(v))

    @property
    def min_gas(self):    return self.data.min_gas
    @min_gas.setter
    def min_gas(self, value):
        self.data.min_gas = value
        k, v = construct_state_key((255, self.id)), self.data.encode()
        self.DB.put(bytes(k), v)
        self.TRIE.update(k, Bytes(v))

    @property
    def num_o(self):    return self.data.num_o
    @num_o.setter
    def num_o(self, value):
        self.data.num_o = value
        k, v = construct_state_key((255, self.id)), self.data.encode()
        self.DB.put(bytes(k), v)
        self.TRIE.update(k, Bytes(v))

    @property
    def num_i(self):    return self.data.num_i
    @num_i.setter
    def num_i(self, value):
        self.data.num_i = value
        k, v = construct_state_key((255, self.id)), self.data.encode()
        self.DB.put(bytes(k), v)
        self.TRIE.update(k, Bytes(v))

    @property
    def t(self):
        return Balance(BASIC_MINIMUM_BALANCE + ADDITIONAL_BALANCE_PER_ITEM * self.num_i + ADDITIONAL_BALANCE_PER_OCTET * self.num_o)

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
        return decode_code_hash(self.lookup[self.code_hash])

    def historical_lookup(self, timeslot: TimeSlot, preimage_hash: ByteArray32):
        """
            https://graypaper.fluffylabs.dev/#/cc517d7/11c70011e000?v=0.6.5
            """
        if (
                self.lookup[preimage_hash] is not None and
                self.is_preimage_valid(
                    self.timestamps[
                        LookupTable(hash=preimage_hash, length=BlobLength(len(self.lookup[preimage_hash])))],
                    timeslot
                )
        ):
            return self.lookup[preimage_hash]
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
        return f"Account(data={self.data})"


class DeltaView:
    def __init__(self, db: KVStore, trie: StateTrie):
        self.DB = db
        self.TRIE = trie

    def __getitem__(self, key: ServiceId):
        data = self.DB.get(bytes(construct_state_key((255, key))))
        return Account(
            id=key,
            db=self.DB,
            trie=self.TRIE,
            data=AccountMetadata.decode_from(data)[0]
        )  if data else data

    def __setitem__(self, key: ServiceId, value: AccountMetadata):
        k, v = construct_state_key((255, key)), value.encode()
        self.DB.put(bytes(k), v)
        self.TRIE.update(k, Bytes(v))

    def __contains__(self, key: ServiceId):
        return self.DB.get(bytes(construct_state_key(255, key))) is not None

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
        k = construct_state_key((self.id, Bytes(U32(key.length).encode()) + key.hash[2:25]))
        v = value.encode()
        self.DB.put(bytes(k), bytes(v))
        self.TRIE.update(k, Bytes(value))
