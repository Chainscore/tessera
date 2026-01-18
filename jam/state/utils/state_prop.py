
from typing import Type
from tsrkit_types import Codable
from .state_key import construct_state_key
from collections import OrderedDict

def make_state_prop(state_key: int, cl: Type[Codable]):
    CAPACITY = 25

    def _get_cache(self):
        if self.store is None:
            raise ValueError("State store is not initialized")
        if state_key not in self.store._prop_cache:
            self.store._prop_cache[state_key] = OrderedDict()
        return self.store._prop_cache[state_key]

    def fget(self):
        cache = _get_cache(self)
        storage_key = construct_state_key(state_key)
        storage_key_bytes = bytes(storage_key)
        raw = self.store.get(storage_key_bytes)
        if raw is None:
            raise ValueError(f"State component missing from DB: {cl.__name__}")
        cache_key = (storage_key_bytes, raw)
        if cache_key in cache:
            cache.move_to_end(cache_key)
            return cache[cache_key]
        decoded_v = cl.decode(raw)
        cache[cache_key] = decoded_v
        if len(cache) > CAPACITY:
            cache.popitem(last=False)
        return decoded_v

    def fset(self, value):
        cache = _get_cache(self)
        k, v = construct_state_key(state_key), value.encode()
        # print("UPDATING KEY", k.hex(), v.hex())
        self.store.put(bytes(k), v)
        storage_key_bytes = bytes(k)
        to_remove = [key for key in cache if key[0] == storage_key_bytes]
        for key in to_remove:
            del cache[key]

    return property(fget, fset)