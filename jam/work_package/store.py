from abc import ABC
from jam.storage.db.kv import KVStore

class DA(ABC):
    db_path: str
    db: KVStore
    prefix: bytes

    def close(self):
        self.db.close()

