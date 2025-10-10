from typing import Self
from collections import OrderedDict

from rockstore import RockStore
from tsrkit_types import Bytes, structure, Dictionary

from jam.block.block import Block
from jam.error import JamError
from jam.finality.finality import Finality
from jam.log_setup import logger
from jam.types.protocol.crypto import StateRoot, HeaderHash, Hash
from jam.utils.trie.merkle import StateTrie

@structure
class Updates:
    prev: Bytes
    curr: Bytes

@structure
class Roots:
    prev: StateRoot
    curr: StateRoot

class StateUpdates(Dictionary[Bytes[31], Updates]):
    ...

@structure
class StateRecord:
    updates: StateUpdates
    roots: Roots


class StateStorage:
    """
    State Store holds current Trie structure with state changes in cache (if any)
    """

    _l_lock = False
    _TRIE: StateTrie
    _DB: RockStore

    _updates: dict[bytes, bytes] = {}
    _cache_mode = False
    _read_only = True
    _prop_cache: dict[int, OrderedDict] = {}

    def __init__(self, trie: StateTrie, db: RockStore, _cache_updates={}, cache_mode = False):
        self._TRIE = trie
        self._DB = db
        self._updates = _cache_updates
        self._cache_mode = cache_mode
        self._prop_cache = {}

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

    def __add__(self, other: "StateStorage") -> Self:
        if not isinstance(other, StateStorage):
            raise TypeError("Can only add StateStorage instances")
        self._updates.update(other._updates)
        return self

    def load_cache(self, hh: HeaderHash, apply_trie: bool = True) -> dict:
        """
        Loads cache for given block's header hash.
        Optionally applies changes in trie of current store's instance.

        Args:
            hh (HeaderHash): block whose cache needs to be stashed.
            apply_trie (bool): flag for applying changes in trie.
        """

        from jam.settings import settings

        kv = settings.main_db
        finalized_block = Finality.load_final(kv)

        if finalized_block is None:
            # NOTE: Genesis Block must be finalized in any case
            raise JamError("State Loading: Not yet initialized")

        fh = finalized_block.header.hash()

        # Load all caches from finalized block till given block
        _updates = {}

        # Exit if block does not exist in our history
        target_block = Block.load(hh, kv)
        if target_block is None:
            return _updates

        # Fetch sync direction.
        # 1 for Ahead of finality. 0 for Behind of finality.
        ahead = target_block.header.slot >= finalized_block.header.slot

        if ahead:
            head_from = hh
            head_to = fh
            use_attr = "curr"
        else:
            head_from = fh
            head_to = hh
            use_attr = "prev"

        records: list[StateRecord] = []

        # Traverse fetched records in sync direction
        curr_head = head_from
        while curr_head != head_to:
            data = kv.get(self.get_storage_key(curr_head))
            if data is None:
                raise ValueError("Updates missing for header:", curr_head.hex())

            records.append(StateRecord.decode(data))

            block = Block.load(curr_head, kv)
            if block is None:
                raise JamError("Block missing for header hash:", curr_head.hex())

            curr_head = block.header.parent

        if ahead:
            records.reverse()

        for record in records:
            roots = record.roots
            final_root = getattr(roots, use_attr)

            trie_updates: dict = {}
            trie_deletes: list = []

            items = record.updates.items()

            # Collect updates
            for k, u in items:
                v = getattr(u, use_attr)

                _updates[k] = v
                if apply_trie:
                    if v == Bytes(0):
                        trie_deletes.append(Bytes(k))
                    else:
                        trie_updates[Bytes[32](k)] = Bytes(v)

            # Apply the cache and verify state root
            if apply_trie and self._TRIE is not None:
                if trie_updates:
                    self._TRIE.batch_update(trie_updates)
                for key in trie_deletes:
                    self._TRIE.delete(key)

                # Sanity Check
                try:
                    assert final_root == self._TRIE.root_hash
                except AssertionError:
                    logger.debug(
                        "Loaded State's Root doesn't match",
                        expected_root=final_root.hex(),
                        actual_root=self._TRIE.root_hash.hex()
                    )

        return _updates

    def record_cache(self, hh: HeaderHash | None = None, kv: RockStore | None = None):
        """
        Apply cached updates to Trie.

        Args:
            hh (HeaderHash): block whose cache needs to be stashed
            kv (RockStore): main DB, where we store blocks
        """

        if self._read_only:
            raise PermissionError("State storage is not writable")

        _state_cache = StateUpdates({})

        prior_root = StateRoot(self._TRIE.root_hash)
        trie_updates = {}
        trie_deletes = []

        if hh:
            block = Block.load(hh, kv)
            previous_updates = self.load_cache(block.header.parent, False)
        else:
            previous_updates = {}

        for k, v in self._updates.items():
            curr_val = self._DB.get(k)

            if k in previous_updates and previous_updates[k] == v:
                continue

            stored_key = Bytes[31](k)

            if kv and hh:
                updates = Updates(
                    prev=Bytes(curr_val) if curr_val else Bytes(0),
                    curr=Bytes(v) if v else Bytes(0)
                )
                _state_cache[stored_key] = updates

            if v is None:
                trie_deletes.append(Bytes(k))
            else:
                trie_updates[Bytes[32](k)] = Bytes(v)

        # Batch process trie updates for better performance
        if trie_updates:
            self._TRIE.batch_update(trie_updates)

        # Process deletes individually (could be optimized further if needed)
        for key in trie_deletes:
            self._TRIE.delete(key)

        posterior_root = StateRoot(self._TRIE.root_hash)
        roots = Roots(
            prev=prior_root,
            curr=posterior_root
        )

        record = StateRecord(updates=_state_cache, roots=roots)
        if kv and hh:
            kv.put(
                self.get_storage_key(hh),
                record.encode(),
            )

    def settle_cache(self):
        """Apply cached updates to DB"""

        if self._read_only:
            raise PermissionError("State storage is not writable")

        for k, v in self._updates.items():
            curr_val = self._DB.get(k)
            if v is None:
                self._DB.delete(k)
            elif v != curr_val:
                self._DB.put(k, v)

        # Clear hash cache periodically to prevent memory buildup
        from jam.types.protocol.crypto import Hash
        Hash.clear_cache()

        # Save the cache to DB
        self.clear()

    def clear(self):
        self._updates = {}
        self._prop_cache = {}

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
