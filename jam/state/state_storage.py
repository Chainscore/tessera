from rockstore import RockStore
from tsrkit_types import Bytes, Dictionary, Option
from jam.state.merkle import StateTrie
from jam.types import HeaderHash, Hash


class StateStorage:
	"""

	cache: dict[key, previous_value]

	"""

	_TRIE: StateTrie
	_DB: RockStore

	_updates: dict[bytes, bytes] = {}
	_cache_mode = False
	_read_only = True

	def __init__(self, trie: StateTrie, db: RockStore, _cache_updates: dict):
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

	def extend_cache(self, __cache: {}): ...

	def save_n_clear_cache(self, kv: RockStore, header: HeaderHash):
		if self._read_only:
			raise PermissionError("State storage is not writable")
		_state_cache = Dictionary[Bytes[31], Bytes]({})
		for k, v in self._updates.items():
			curr_val = self._DB.get(k)
			_state_cache[Bytes[31](k)] = Bytes(curr_val) if curr_val else Bytes(0)
			if v is None:
				self._DB.delete(k)
				self._TRIE.delete(Bytes(k))
			else:
				self._DB.put(k, v)
				self._TRIE.update(Bytes(k), Bytes(v))
		# Save the cache to DB
		self._updates = {}
		# State cache to store in DB
		kv.put(self.get_storage_key(header), _state_cache.encode())

	def put(self, key_bytes: bytes, value_bytes: bytes, sync: bool = False):
		if self._cache_mode:
			self._updates[key_bytes] = value_bytes
		else:
			self._DB.put(key_bytes, value_bytes, sync)
			self._TRIE.update(Bytes(key_bytes), Bytes(value_bytes))

	def get(self, key_bytes: bytes, fill_cache: bool = True, skip_cache = False) -> bytes | None:
		if key_bytes in self._updates.keys() and not skip_cache:
			return self._updates[key_bytes]
		return self._DB.get(key_bytes, fill_cache)

	def delete(self, key_bytes: bytes, sync = False):
		if self._cache_mode:
			self._updates[key_bytes] = None
		else:
			self._DB.delete(key_bytes, sync)
			self._TRIE.delete(Bytes(key_bytes))
