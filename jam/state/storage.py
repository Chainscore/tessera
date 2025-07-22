from typing import TYPE_CHECKING, Final

from jam.block.block import Block
from jam.error import JamError
from jam.finality.finality import Finality

from rockstore import RockStore
from jam.types.protocol.crypto import OpaqueHash
from tsrkit_types import Bytes, structure, Dictionary
from jam.utils.trie.merkle import StateTrie
from jam.types import HeaderHash, Hash


class StateUpdates(Dictionary[Bytes[31], Bytes]):
    ...


@structure
class StateRecord:
    updates: StateUpdates
    root: OpaqueHash


class StateStorage:
    """

    cache: dict[key, previous_value]

    """

    # Past state load lock, we can only load one past state at a time
    _l_lock = False

    _TRIE: StateTrie
    _DB: RockStore

    _updates: dict[bytes, bytes] = {}
    _cache_mode = False
    _read_only = True

    def __init__(self, trie: StateTrie, db: RockStore, _cache_updates={}):
        self._TRIE = trie
        self._DB = db
        self._updates = _cache_updates

    @staticmethod
    def get_storage_key(header: HeaderHash):
        return Hash.blake2b("STORAGE_CACHE".encode() + header)

    def enable_writes(self):
        self._read_only = False

    def enable_cache(self):
        self._cache_mode = True

    def disable_cache(self):
        if len(self._updates) != 0:
            raise ValueError("Cache is not empty")
        self._cache_mode = False

    def _load_updates(self, header: HeaderHash) -> dict:
        # 1. Load all caches from current head to mentioned header
        from jam.settings import settings

        kv = settings.main_db

        latest_block = Finality.load_latest(kv)
        if latest_block is None:
            return {}
            # raise JamError("LoadUpdates: Not is not yet initialized")

        curr_head = latest_block.header.parent

        _updates = {}

        # Exit if block does not exists in our history
        if Block.load(header, kv) == None:
            return _updates

        while curr_head != header:
            data = kv.get(self.get_storage_key(curr_head))
            if data is None:
                raise ValueError("Updates missing for", curr_head)
            _curr_updates = StateRecord.decode(data)
            block = Block.load(curr_head, kv)
            if block is None:
                raise JamError("Block missing for header hash:", curr_head)
            curr_head = block.header.parent

            # 2. Join them one after another (overwriting) to get one cache record
            for k, v in _curr_updates.updates.items():
                _updates[k] = v

        return _updates

    def save_n_clear_cache(self, hh: HeaderHash | None = None, kv: RockStore | None = None):
        """
        Apply cached updates to the State DB + Trie

        Args:
            kv: DB where we store
        """
        if self._read_only:
            raise PermissionError("State storage is not writable")
        _state_cache = StateUpdates({})
        for k, v in self._updates.items():
            curr_val = self._DB.get(k)
            if kv and hh:
                _state_cache[Bytes[31](k)] = Bytes(curr_val) if curr_val else Bytes(0)
            if v is None:
                self._DB.delete(k)
                self._TRIE.delete(Bytes(k))
            elif curr_val != v:
                self._DB.put(k, v)
                self._TRIE.update(Bytes(k), Bytes(v))
        # Save the cache to DB
        self._updates = {}
        # State cache to store in DB
        if kv and hh:
            kv.put(
                self.get_storage_key(hh),
                StateRecord(updates=_state_cache, root=Bytes[32](self._TRIE.root_hash)).encode(),
            )

    def clear(self):
        self._updates = {}

    def put(self, key_bytes: bytes, value_bytes: bytes, sync: bool = False):
        if self._cache_mode:
            self._updates[key_bytes] = value_bytes
        else:
            self._DB.put(key_bytes, value_bytes, sync)
            self._TRIE.update(Bytes(key_bytes), Bytes(value_bytes))

    def get(self, key_bytes: bytes, fill_cache: bool = True, skip_cache=False) -> bytes | None:
        if key_bytes in self._updates.keys() and not skip_cache:
            return self._updates[key_bytes]
        return self._DB.get(key_bytes, fill_cache)

    def delete(self, key_bytes: bytes, sync=False):
        if self._cache_mode:
            self._updates[key_bytes] = None
        else:
            self._DB.delete(key_bytes, sync)
            self._TRIE.delete(Bytes(key_bytes))
