import asyncio
from keyword import kwlist
from typing import Tuple

from rockstore import store
from jam.execution.utils import decode_code_hash
from jam.state.storage import StateStorage
from jam.state.utils import construct_state_key
from jam.types.protocol.core import Balance, ServiceId, TimeSlot, BlobLength
from jam.types.protocol.crypto import Hash
from jam.types.state.delta import (
    AccountMetadata,
    Ai,
    Ao,
    LookupTable,
    Timestamps,
    AccountData,
)
from jam.utils.constants import (
    BASIC_MINIMUM_BALANCE,
    ADDITIONAL_BALANCE_PER_ITEM,
    ADDITIONAL_BALANCE_PER_OCTET,
)
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U32
from jam.api.rpc.subscription_handlers import (
    subscribe_service_value,
    subscribe_service_request,
    subscribe_service_data,
    subscribe_service_preimage
)


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
        # Publishes updates of the service data.
        asyncio.create_task(subscribe_service_data(self.id, meta))

    return property(getter, setter)


class AccountDataView:
    def __init__(self, id: ServiceId, store: StateStorage):
        self.id = id
        self.store = store

    code_hash   = make_account_prop("code_hash")
    balance     = make_account_prop("balance")
    gas_limit   = make_account_prop("gas_limit")  # min_item_gas
    min_gas     = make_account_prop("min_gas")  # min_memo_gas
    num_o       = make_account_prop("num_o")
    gratis_offset = make_account_prop("gratis_offset")
    num_i       = make_account_prop("num_i")
    created_at  = make_account_prop("created_at")
    accumulated_at = make_account_prop("accumulated_at")
    parent_service = make_account_prop("parent_service")

    @property
    def t(self):
        return Balance(max(0, 
            BASIC_MINIMUM_BALANCE
            + ADDITIONAL_BALANCE_PER_ITEM * self.num_i
            + ADDITIONAL_BALANCE_PER_OCTET * self.num_o
            - self.gratis_offset
        ))


class Account:
    def __init__(self, id: ServiceId, store: StateStorage):
        self.id = id
        self.store = store

    @property
    def t(self):
        return Balance(max(0, 
            BASIC_MINIMUM_BALANCE
            + ADDITIONAL_BALANCE_PER_ITEM * self.service.num_i
            + ADDITIONAL_BALANCE_PER_OCTET * self.service.num_o
            - self.service.gratis_offset
        ))

    @property
    def service(self):
        return AccountDataView(self.id, self.store)

    @service.setter
    def service(self, value: AccountMetadata):
        storage_key, encoded_val = (
            bytes(construct_state_key((255, self.id))),
            value.encode(),
        )
        self.store.put(storage_key, encoded_val)
        # Publishes updates of the service data.
        asyncio.create_task(subscribe_service_data(self.id, value))
        
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
        if not self.service.code_hash:
            return None
        img = self.preimages.get(self.service.code_hash)
        if img:
            try:
                return decode_code_hash(img)
            except:
                return None
        else:
            return None

    def historical_lookup(self, timeslot: TimeSlot, preimage_hash: Bytes[32]):
        """
        https://graypaper.fluffylabs.dev/#/38c4e62/11fa0011fa00?v=0.7.0
        """
        if self.preimages[preimage_hash] is not None and self.is_preimage_valid(
            self.lookup[
                LookupTable(
                    hash=preimage_hash,
                    length=BlobLength(len(self.preimages[preimage_hash])),
                )
            ],
            timeslot,
        ):
            return self.preimages[preimage_hash]
        else:
            return None

    @classmethod
    def is_preimage_valid(cls, lookup_ts: Timestamps, current_ts: TimeSlot):
        """
        https://graypaper.fluffylabs.dev/#/38c4e62/114301114301?v=0.7.0
        """
        if not lookup_ts:
            return False
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
        for k, v in value.preimages.items():
            account.preimages[k] = v
        for k, v in value.storage.items():
            account.storage[k] = v
        for k, v in value.lookup.items():
            account.lookup[k] = v

    def __contains__(self, key: ServiceId):
        return self.store.get(bytes(construct_state_key((255, key)))) is not None
    
    def __delitem__(self, key: ServiceId):
        account_s_key = bytes(construct_state_key((255, key)))
        self.store.delete(account_s_key)

class StorageView:
    def __init__(self, id: ServiceId, store: StateStorage):
        self.id = id
        self.store = store

    def __getitem__(self, key: Bytes):
        data = self.store.get(self.get_key(key))
        return Bytes(data) if data else data

    def get(self, key):
        return self.__getitem__(key)

    def get_key(self, key: Bytes):
        return bytes(construct_state_key((self.id, Bytes(U32(2**32 - 1).encode()) + key)))

    def __setitem__(self, key: Bytes, value: Bytes):
        # TODO - check for gas before adding, throw error if insufficient. This is supposed to be handled in relevent invocation
        storage_key = self.get_key(key)
        curr_data = self[key]
        meta_view = AccountDataView(self.id, self.store)
        if curr_data is None:
            meta_view.num_i = meta_view.num_i + 1
            meta_view.num_o = meta_view.num_o + len(value) + 34 + len(key)
        else:
            meta_view.num_o = meta_view.num_o + len(value) - len(curr_data)
        # Publishes updates for service value
        asyncio.create_task(subscribe_service_value(self.id, key, list(value)))
        self.store.put(storage_key, value)

    def __delitem__(self, key: Bytes):
        curr_value = self[key]
        storage_key = self.get_key(key)
        if curr_value:
            meta_view = AccountDataView(self.id, self.store)
            meta_view.num_i = meta_view.num_i - 1
            meta_view.num_o = meta_view.num_o - len(curr_value) - 34 - len(key)
        # Publishes updates for service value
        asyncio.create_task(subscribe_service_value(self.id, key, None))

        self.store.delete(storage_key)


class PreImageView:
    def __init__(self, id: ServiceId, store: StateStorage):
        self.id = id
        self.store = store

    def __getitem__(self, key: Bytes[32]):
        data = self.store.get(self.get_key(key))
        return Bytes(data) if data else data

    def get(self, key):
        return self.__getitem__(key)

    def get_key(self, key: Bytes):
        return bytes(construct_state_key((self.id, Bytes(U32(2**32 - 2).encode()) + key)))

    def __setitem__(self, key: Bytes[32], value: Bytes):
        k = self.get_key(key)
        self.store.put(k, value)
        # Publishes updates for service preimage
        asyncio.create_task(subscribe_service_preimage(self.id, key, value))

    def __delitem__(self, key: Bytes[32]):
        storage_key = self.get_key(key)
        # Publishes updates for service preimage
        asyncio.create_task(subscribe_service_preimage(self.id, key, None))

        self.store.delete(storage_key)



class TimestampsView:
    def __init__(self, id: ServiceId, store: StateStorage):
        self.id = id
        self.store = store

    def __getitem__(self, key: LookupTable):
        storage_key = self.get_key(key)
        data = self.store.get(storage_key)
        return Timestamps.decode(data) if data else data

    def get(self, key):
        return self.__getitem__(key)

    def get_key(self, key: LookupTable):
        return bytes(construct_state_key((self.id, Bytes(U32(key.length).encode()) + key.hash)))

    def __setitem__(self, key: LookupTable, value: Timestamps):
        storage_key = self.get_key(key)
        v = value.encode()

        curr_data = self.store.get(storage_key)
        meta_view = AccountDataView(self.id, self.store)
        if curr_data is None:
            meta_view.num_i = meta_view.num_i + 2
            meta_view.num_o = meta_view.num_o + key.length + 81
        # Publishes updates for service request
        asyncio.create_task(subscribe_service_request(self.id, key.hash, key.length, value))

        self.store.put(storage_key, v)

    def __delitem__(self, key: LookupTable):
        storage_key = self.get_key(key)
        curr_data = self.store.get(storage_key)
        if curr_data is not None:
            meta_view = AccountDataView(self.id, self.store)
            meta_view.num_i = meta_view.num_i - 2
            meta_view.num_o = meta_view.num_o - key.length - 81
        # Publishes updates for service request
        asyncio.create_task(subscribe_service_request(self.id, key.hash, key.length, None))

        self.store.delete(storage_key)
