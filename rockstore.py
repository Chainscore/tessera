"""Minimal in-memory replacement for the external `rockstore` KV database.

Only a handful of helper methods (`get`, `put`) are needed by the types
package to load and store blocks during unit tests and examples.  This
implementation backs the data store with a plain Python dictionary so it
requires zero native dependencies.
"""

from __future__ import annotations

from threading import RLock


class RockStore:  # noqa: D401
    """Very small subset of the RocksDB API used by the codebase."""

    def __init__(self):
        self._lock = RLock()
        self._data: dict[bytes, bytes] = {}

    # ---------------------------------------------------------------------
    # Basic key-value helpers
    # ---------------------------------------------------------------------

    def get(self, key: bytes) -> bytes | None:  # noqa: D401
        with self._lock:
            return self._data.get(key)

    def put(self, key: bytes, value: bytes) -> None:  # noqa: D401
        with self._lock:
            self._data[key] = value

    # Mirrors the behaviour of RocksDB’s `put` when `value is None`.
    def delete(self, key: bytes) -> None:  # noqa: D401
        with self._lock:
            self._data.pop(key, None)

    # Convenience so that `with RockStore() as db:` works if ever used.
    def __enter__(self):  # noqa: D401
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: D401
        # Nothing to clean up for in-memory store.
        pass