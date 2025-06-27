from abc import ABC

from rockstore import RockStore


class DA(ABC):
    db_path: str
    db: RockStore
    prefix: bytes

    def close(self):
        self.db.close()

