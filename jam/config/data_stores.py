from rockstore import RockStore

class DataStores:
    _main_db: RockStore | None
    _state_db: RockStore | None
    _audit_db: RockStore | None
    _d3l: RockStore | None

    def __init__(self):
        self._main_db, self._state_db, self._audit_db, self._d3l  = None, None, None, None

    @property
    def main_db(self) -> RockStore:
        if not self._main_db:
            raise ValueError("DB Paths are not set, call configure_db_paths before this.")
        return self._main_db

    @property
    def audit_da(self) -> RockStore:
        if not self._audit_db:
            raise ValueError("DB Paths are not set, call configure_db_paths before this.")
        return self._audit_db

    @property
    def d3l(self) -> RockStore:
        if not self._d3l:
            raise ValueError("DB Paths are not set, call configure_db_paths before this.")
        return self._d3l

    @property
    def state_db(self) -> RockStore:
        if not self._state_db:
            raise ValueError("DB Paths are not set, call configure_db_paths before this.")
        return self._state_db

    def configure_db_paths(self, parent_path = "data"):
        self._main_db = RockStore(parent_path+"/main")
        self._audit_db = RockStore(parent_path+"/audit")
        self._d3l = RockStore(parent_path+"/d3l")
        self._state_db = RockStore(parent_path+"/state")


data_stores = DataStores()