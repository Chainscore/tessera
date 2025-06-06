from rockstore import RockStore

class DataStores:
    _main_db: RockStore | None
    _audit_db: RockStore | None
    _d3l: RockStore | None

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

    def configure_db_paths(self, parent_path = "data"):
        self._main_db = RockStore(parent_path+"/main")
        self._audit_db = RockStore(parent_path+"/audit")
        self._d3l = RockStore(parent_path+"/d3l")


data_stores = DataStores()