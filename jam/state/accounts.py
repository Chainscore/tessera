from dataclasses import dataclass

from jam.storage.db.kv import KVStore
from jam.state.merkle import StateTrie
from jam.state.utils.key_constructor import construct_state_key
from jam.types.base import Bytes, ByteArray32, U32
from jam.types.protocol.core import Balance, Gas, ServiceId
from jam.types.state.delta import ServiceCodeHash, Ao, Ai, LookupTable, Timestamps
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.utils.codec.primitives.bytes import BytesCodec
from jam.utils.json import JsonSerde
from jam.utils.constants import BASIC_MINIMUM_BALANCE, ADDITIONAL_BALANCE_PER_ITEM, ADDITIONAL_BALANCE_PER_OCTET


@dataclass
@decodable_dataclass
class AccountMetadata(Codable, JsonSerde):
    code_hash: ServiceCodeHash  # code_hash
    balance: Balance  # balance
    gas_limit: Gas  # min_item_gas
    min_gas: Gas  # min_memo_gas
    num_o: Ao
    num_i: Ai


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
    def lookup(self):
        return PreImageView(self.id, self.DB, self.TRIE)

    @property
    def timestamps(self):
        return TimestampsView(self.id, self.DB, self.TRIE)

    def m_c(self) -> (bytes, bytes):
        service_data = self.lookup[self.code_hash])
        pm, offset = BytesCodec.decode_from(service_data)
        pc = service_data[offset:]
        return pm, pc


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
        data = self.DB.get(bytes(construct_state_key((self.id, ByteArray32(Bytes(U32(2**32 - 1).encode()) + key[0:28])))))
        return Bytes(data) if data else data

    def __setitem__(self, key: ByteArray32, value: Bytes):
        k = construct_state_key((self.id, ByteArray32(Bytes(U32(2 ** 32 - 1).encode()) + key[0:28])))
        # TODO - check for gas before adding, throw error if insufficient. This is supposed to be handled in relevent invocation
        self.DB.put(
            bytes(k),
            bytes(value)
        )
        self.TRIE.update(k, value)
        # TODO - update ai, ao

    def __delitem__(self, key):
        self.DB.delete(bytes(key))
        #TODO: Implement trie update once trie can delete nodes
        raise ValueError("Not yet implemented. Contact Prasad")

class PreImageView:
    def __init__(self, id: ServiceId, db: KVStore, trie: StateTrie):
        self.id = id
        self.DB = db
        self.TRIE = trie

    def __getitem__(self, key: ByteArray32):
        data = self.DB.get(bytes(construct_state_key((self.id, ByteArray32(Bytes(U32(2**32 - 2).encode()) + key[1:29])))))
        return Bytes(data) if data else data

    def __setitem__(self, key: ByteArray32, value: Bytes):
        k = construct_state_key((self.id, ByteArray32(Bytes(U32(2 ** 32 - 2).encode()) + key[1:29])))
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
        data = self.DB.get(bytes(construct_state_key((self.id, ByteArray32(Bytes(U32(key.length).encode()) + key.hash[2:30])))))
        return Timestamps.decode_from(data)[0] if data else data

    def __setitem__(self, key: LookupTable, value: Timestamps):
        k = construct_state_key((self.id, ByteArray32(Bytes(U32(key.length).encode()) + key.hash[2:30])))
        v = value.encode()
        self.DB.put(bytes(k), bytes(v))
        self.TRIE.update(k, Bytes(value))
