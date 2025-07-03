from typing import Tuple
from jam.execution.utils import decode_code_hash
from jam.state.storage import StateStorage
from jam.state.utils import construct_state_key
from jam.types.protocol.core import Balance, ServiceId, TimeSlot, BlobLength
from jam.types.protocol.crypto import Hash
from jam.types.state.delta import AccountMetadata, LookupTable, Timestamps, AccountData
from jam.utils.constants import BASIC_MINIMUM_BALANCE, ADDITIONAL_BALANCE_PER_ITEM, ADDITIONAL_BALANCE_PER_OCTET
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U32

def make_account_prop(field):
    def getter(self):
        data = self.store.get(bytes(construct_state_key((255, self.id))))
        if data is None:
            return None
        meta = AccountMetadata.decode(data)
        return getattr(meta, field)
    def setter(self, value):
        data = self.store.get(bytes(construct_state_key((255, self.id))))
        if data is None:
            return
        meta = AccountMetadata.decode(data)
        setattr(meta, field, value)
        k, v = construct_state_key((255, self.id)), meta.encode()
        self.store.put(k, v)
    return property(getter, setter)


class AccountDataView:
    def __init__(self, id: ServiceId, store: StateStorage):
        self.id = id
        self.store = store

    code_hash = make_account_prop('code_hash')
    balance = make_account_prop('balance')
    gas_limit = make_account_prop('gas_limit')  # min_item_gas
    min_gas = make_account_prop('min_gas')  # min_memo_gas
    num_o = make_account_prop('num_o')
    num_i = make_account_prop('num_i')

    @property
    def t(self):
        return Balance(
            BASIC_MINIMUM_BALANCE + ADDITIONAL_BALANCE_PER_ITEM * self.num_i + ADDITIONAL_BALANCE_PER_OCTET * self.num_o
        )


class Account:

    def __init__(self, id: ServiceId, store: StateStorage):
        self.id = id
        self.store = store

    @property
    def t(self):
        return Balance(BASIC_MINIMUM_BALANCE + ADDITIONAL_BALANCE_PER_ITEM * self.service.num_i + ADDITIONAL_BALANCE_PER_OCTET * self.service.num_o)

    @property
    def service(self):
        return AccountDataView(self.id, self.store)

    @service.setter
    def service(self, value: AccountMetadata):
        storage_key, encoded_val = bytes(construct_state_key((255, self.id))), value.encode()
        self.store.put(storage_key, encoded_val)

    @property
    def storage(self):
        return StorageView(self.id, self.store)

    @property
    def preimages(self):
        return PreImageView(self.id, self.store)

    @property
    def lookup(self):
        return TimestampsView(self.id, self.store)

    def m_c(self) -> Tuple[bytes, bytes]:
        return decode_code_hash(self.preimages[self.service.code_hash])

    def historical_lookup(self, timeslot: TimeSlot, preimage_hash: Bytes[32]):
        """
        https://graypaper.fluffylabs.dev/#/cc517d7/11c70011e000?v=0.6.5
        """
        if (
                self.preimages[preimage_hash] is not None and
                self.is_preimage_valid(
                    self.lookup[
                        LookupTable(hash=preimage_hash, length=BlobLength(len(self.preimages[preimage_hash])))
                    ],
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
            return lookup_ts[0] <= current_ts
        elif len(lookup_ts) == 2:
            return lookup_ts[0] <= current_ts < lookup_ts[1]
        elif len(lookup_ts) == 3:
            return (lookup_ts[0] <= current_ts < lookup_ts[1]) or lookup_ts[2] <= current_ts
        else:
            raise ValueError("Invalid Timestamp data")

    def __repr__(self):
        return f"Account(id={self.id})"


class DeltaView:
    def __init__(self, store: StateStorage):
        self.store = store

    def __getitem__(self, key: ServiceId):
        return Account(id=key, store=self.store)

    def __setitem__(self, key: ServiceId, value: AccountData):
        account = Account(id=key, store=self.store)
        account.service = value.service
        for k,v in value.preimages:
            account.preimages[k] = v
        for k, v in value.storage:
            account.storage[k] = v
        for k, v in value.lookup:
            account.lookup[k] = v

    def __contains__(self, key: ServiceId):
        return self.store.get(bytes(construct_state_key((255, key)))) is not None

class StorageView:
    def __init__(self, id: ServiceId, store: StateStorage):
        self.id = id
        self.store = store

    def __getitem__(self, key: Bytes[32]):
        data = self.store.get(bytes(construct_state_key((self.id, Bytes(U32(2**32 - 1).encode()) + key[0:23]))))
        return Bytes(data) if data else data

    def __setitem__(self, key: Bytes[32], value: Bytes):
        # TODO - check for gas before adding, throw error if insufficient. This is supposed to be handled in relevent invocation
        key = construct_state_key((self.id, Bytes(U32(2 ** 32 - 1).encode()) + key[0:23]))
        curr_data = self.store.get(bytes(key))
        meta_view = AccountDataView(self.id, self.store)
        if curr_data is None:
            meta_view.num_i = meta_view.num_i + 1
            meta_view.num_o = meta_view.num_o + len(value) + 32
        else:
            meta_view.num_o =meta_view.num_o + len(value) - len(curr_data)

        self.store.put(key, value)

    def __delitem__(self, key: Bytes[32]):
        curr_value = self[key]
        if curr_value:
            meta_view = AccountDataView(self.id, self.store)
            meta_view.num_i = meta_view.num_i - 1
            meta_view.num_o = meta_view.num_o - len(curr_value) - 32
        storage_key = construct_state_key((self.id, Bytes(U32(2 ** 32 - 1).encode()) + key[0:23]))
        self.store.delete(storage_key)

class PreImageView:
    def __init__(self, id: ServiceId, store: StateStorage):
        self.id = id
        self.store = store

    def __getitem__(self, key: Bytes[32]):
        data = Bytes(U32(2**32 - 2).encode() + bytes(key)[1:24])
        data = self.store.get(construct_state_key((self.id, data)))
        return Bytes(data) if data else data

    def __setitem__(self, key: Bytes[32], value: Bytes):
        k = construct_state_key((self.id, Bytes(U32(2 ** 32 - 2).encode()) + key[1:24]))
        self.store.put(k, value)

    def __delitem__(self, key: Bytes[32]):
        storage_key = construct_state_key((self.id, Bytes(U32(2 ** 32 - 2).encode()) + key[1:24]))
        self.store.delete(storage_key)

class TimestampsView:
    def __init__(self, id: ServiceId, store: StateStorage):
        self.id = id
        self.store = store

    def __getitem__(self, key: LookupTable):
        storage_key = construct_state_key((self.id, Bytes(U32(key.length).encode()) + Hash.blake2b(bytes(key.hash))[2:25]))
        data = self.store.get(storage_key)
        return Timestamps.decode(data) if data else data

    def __setitem__(self, key: LookupTable, value: Timestamps):
        storage_key = construct_state_key((self.id, Bytes(U32(key.length).encode()) + Hash.blake2b(bytes(key.hash))[2:25]))
        v = value.encode()

        curr_data = self.store.get(storage_key)
        meta_view = AccountDataView(self.id, self.store)
        if curr_data is None:
            meta_view.num_i = meta_view.num_i + 2
            meta_view.num_o = meta_view.num_o + key.length + 81

        self.store.put(storage_key, v)

    def __delitem__(self, key: LookupTable):
        storage_key = construct_state_key((self.id, Bytes(U32(key.length).encode()) + Hash.blake2b(bytes(key.hash))[2:25]))
        curr_data = self.store.get(storage_key)
        if curr_data is not None:
            meta_view = AccountDataView(self.id, self.store)
            meta_view.num_i = meta_view.num_i - 2
            meta_view.num_o = meta_view.num_o - key.length - 81

        self.store.delete(storage_key)
