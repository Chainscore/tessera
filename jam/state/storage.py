from typing import Self
from collections import OrderedDict

from rockstore import RockStore
from tsrkit_types import Bytes, structure, Dictionary, Null, Option

from jam.block.block import Block
from jam.error import JamError
from jam.finality.finality import Finality
from jam.log_setup import logger
from jam.models.protocol.crypto import StateRoot, HeaderHash, Hash
from jam.utils.trie.merkle import StateTrie

Bytes31 = Bytes[31]
Bytes32 = Bytes[32]
StateUpdateValue = Option[Bytes]
_MISSING = object()


@structure
class Updates:
    prev: StateUpdateValue
    curr: StateUpdateValue


@structure
class Roots:
    prev: StateRoot
    curr: StateRoot


class StateUpdates(Dictionary[Bytes31, Updates]): ...


@structure
class StateRecord:
    updates: StateUpdates
    roots: Roots


def _encode_update_value(value: bytes | None) -> StateUpdateValue:
    return StateUpdateValue(Null if value is None else Bytes(value))


def _decode_update_value(value: StateUpdateValue) -> bytes | None:
    unwrapped = value.unwrap()
    if unwrapped == Null:
        return None
    return bytes(unwrapped)


class StateStorage:
    """
    State Store holds current Trie structure with state changes in cache (if any)
    """

    _l_lock = False
    _TRIE: StateTrie
    _DB: RockStore

    _updates: dict[bytes, bytes]
    _cache_mode = False
    _read_only = True
    _prop_cache: dict[int, OrderedDict]

    def __init__(
        self,
        trie: StateTrie,
        db: RockStore,
        _cache_updates=None,
        cache_mode=False,
        inherited_keys=None,
    ):
        self._TRIE = trie
        self._DB = db
        self._updates = _cache_updates if _cache_updates is not None else {}
        self._base_updates = self._updates.copy()
        self._cache_mode = cache_mode
        self._prop_cache = {}
        # Keys that existed before this store was created (inherited from parent clone)
        # Only applies to cloned stores - used to filter merge to only include new writes
        self._inherited_keys = inherited_keys or set()

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
        # Only merge keys that are NOT inherited (i.e., new writes during this accumulation)
        new_writes = {k: v for k, v in other._updates.items() if k not in other._inherited_keys}
        self._updates.update(new_writes)
        return self

    def load_cache(self, hh: HeaderHash, apply_trie: bool = True) -> tuple[dict, StateRoot | None]:
        """
        Loads cache for given block's header hash.
        Optionally applies changes in trie of current store's instance.

        Args:
            hh (HeaderHash): block whose cache needs to be stashed.
            apply_trie (bool): flag for applying changes in trie.

        Returns:
            Tuple of (updates dict, final_root). final_root is the expected
            state root after applying all updates.
        """
        if hh == HeaderHash(32):
            return {}, None

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
        target_header = Block.load_header(hh, kv)
        if target_header is None:
            return _updates, None

        # Fetch sync direction.
        # 1 for Ahead of finality. 0 for Behind of finality.
        ahead = target_header.slot >= finalized_block.header.slot

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
                # No StateRecord for this block - we've likely reached genesis
                # or a block before our stored history. Stop traversing.
                break

            records.append(StateRecord.decode(data))

            parent_hash = Block.load_parent_hash(curr_head, kv)
            if parent_hash is None:
                raise JamError("Block missing for header hash:", curr_head.hex())

            # Stop if we've reached genesis (parent is zero hash)
            if parent_hash == HeaderHash(32):
                break

            curr_head = parent_hash

        if ahead:
            records.reverse()

        final_root = None
        for record in records:
            roots = record.roots
            final_root = getattr(roots, use_attr)

            trie_updates: dict = {}
            trie_deletes: list = []

            items = record.updates.items()

            # Collect updates
            for k, u in items:
                v = getattr(u, use_attr)
                normalized_v = _decode_update_value(v)

                _updates[k] = normalized_v
                if apply_trie:
                    if normalized_v is None:
                        trie_deletes.append(Bytes(k))
                    else:
                        trie_updates[Bytes32(k)] = Bytes(normalized_v)

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
                        actual_root=self._TRIE.root_hash.hex(),
                    )

        if apply_trie and self._TRIE is not None:
            self._TRIE.prune_unreachable()

        return _updates, final_root

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
            parent_hash = Block.load_parent_hash(hh, kv)
            if parent_hash is None:
                raise JamError("Block missing for header hash:", hh.hex())
            previous_updates = self._base_updates
        else:
            previous_updates = {}

        for k, v in self._updates.items():
            curr_val = self._DB.get(k)
            prev_val = previous_updates.get(k, curr_val)

            if k in previous_updates and previous_updates[k] == v:
                continue

            stored_key = Bytes31(k)

            if kv and hh:
                updates = Updates(
                    prev=_encode_update_value(prev_val),
                    curr=_encode_update_value(v),
                )
                _state_cache[stored_key] = updates

            if v is None:
                trie_deletes.append(Bytes(k))
            else:
                trie_updates[Bytes32(k)] = Bytes(v)

        # Batch process trie updates for better performance
        if trie_updates:
            self._TRIE.batch_update(trie_updates)

        # Process deletes individually (could be optimized further if needed)
        for key in trie_deletes:
            self._TRIE.delete(key)

        self._TRIE.prune_unreachable()

        posterior_root = StateRoot(self._TRIE.root_hash)
        roots = Roots(prev=prior_root, curr=posterior_root)

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
        from jam.models.protocol.crypto import Hash

        Hash.clear_cache()

        # Save the cache to DB
        self.clear()

    def clear(self):
        self._updates = {}
        self._base_updates = {}
        self._prop_cache = {}

    def put(self, key_bytes: bytes, value_bytes: bytes, sync: bool = False):
        if self._cache_mode:
            self._updates[key_bytes] = value_bytes
            # Key is now explicitly written, not inherited - include in merge
            self._inherited_keys.discard(key_bytes)
        else:
            self._DB.put(key_bytes, value_bytes, sync)
            self._TRIE.update(Bytes(key_bytes), Bytes(value_bytes))

    def get(self, key_bytes: bytes, fill_cache: bool = True, skip_cache=False) -> bytes | None:
        if not skip_cache:
            cached = self._updates.get(key_bytes, _MISSING)
            if cached is not _MISSING:
                return cached
        return self._DB.get(key_bytes, fill_cache)

    def delete(self, key_bytes: bytes, sync=False):
        if self._cache_mode:
            self._updates[key_bytes] = None
            # Deleted inherited keys must still be merged back as explicit writes.
            self._inherited_keys.discard(key_bytes)
        else:
            self._DB.delete(key_bytes, sync)
            self._TRIE.delete(Bytes(key_bytes))
