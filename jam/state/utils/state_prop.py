
from typing import Type
from tsrkit_types import Codable
from .state_key import construct_state_key
from collections import OrderedDict

def make_state_prop(state_key: int, cl: Type[Codable]):
    CAPACITY = 25
    storage_key_bytes = bytes(construct_state_key(state_key))
    component_name = cl.__name__

    def fget(self):
        store = self.store
        if store is None:
            raise ValueError("State store is not initialized")
        prop_cache = store._prop_cache
        cache = prop_cache.get(state_key)
        if cache is None:
            cache = OrderedDict()
            prop_cache[state_key] = cache
        raw = store.get(storage_key_bytes)
        if raw is None:
            raise ValueError(f"State component missing from DB: {component_name}")
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
        store = self.store
        if store is None:
            raise ValueError("State store is not initialized")
        prop_cache = store._prop_cache
        cache = prop_cache.get(state_key)
        if cache is None:
            cache = OrderedDict()
            prop_cache[state_key] = cache
        v = value.encode()
        store.put(storage_key_bytes, v)
        cache.clear()

    return property(fget, fset)
