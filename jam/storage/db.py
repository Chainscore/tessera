from abc import ABC, abstractmethod
from typing import Optional, Iterator
import rocksdb
from pathlib import Path


class Database(ABC):
    @abstractmethod
    def get(self, key: bytes) -> Optional[bytes]:
        pass

    @abstractmethod
    def put(self, key: bytes, value: bytes) -> None:
        pass

    @abstractmethod
    def delete(self, key: bytes) -> None:
        pass

    @abstractmethod
    def iterator(self, prefix: bytes) -> Iterator[tuple[bytes, bytes]]:
        pass


class RocksDatabase(Database):
    def __init__(self, path: Path):
        opts = rocksdb.Options()
        opts.create_if_missing = True
        opts.max_open_files = 300000
        opts.write_buffer_size = 67108864
        opts.max_write_buffer_number = 3
        opts.target_file_size_base = 67108864

        self.db = rocksdb.DB(str(path), opts)

    def get(self, key: bytes) -> Optional[bytes]:
        return self.db.get(key)

    def put(self, key: bytes, value: bytes) -> None:
        self.db.put(key, value)

    def delete(self, key: bytes) -> None:
        self.db.delete(key)

    def iterator(self, prefix: bytes) -> Iterator[tuple[bytes, bytes]]:
        it = self.db.iteritems()
        it.seek(prefix)
        while it.valid():
            key = it.get()[0]
            if not key.startswith(prefix):
                break
            yield it.get()
            it.next()
