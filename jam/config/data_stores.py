from rockstore import RockStore

class DataStores:
    _main_db: RockStore | None
    _state_db: RockStore | None
    _audit_db: RockStore | None
    _d3l: RockStore | None

    def __init__(self):
        self._main_db = None
        self._audit_db = None
        self._d3l = None
        self._state_db = None

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

    def configure_db_paths(self, parent_path=""):
        import os
        from jam.config.settings import settings
        self.shutdown()

        os.makedirs(parent_path + settings.DB_PATH, exist_ok=True)
        os.makedirs(parent_path + settings.D3L_PATH, exist_ok=True)
        os.makedirs(parent_path + settings.AUDIT_DB_PATH, exist_ok=True)
        os.makedirs(parent_path + "/state", exist_ok=True)

        self._main_db = RockStore(parent_path + settings.DB_PATH)
        self._audit_db = RockStore(parent_path + settings.D3L_PATH)
        self._d3l = RockStore(parent_path + settings.AUDIT_DB_PATH)
        self._state_db = RockStore(parent_path + "/state")

    def shutdown(self):
        if self._main_db:
            self._main_db.close()
            print("Closing main db")
        if self._d3l:
            self._d3l.close()
            print("Closing d3l db")
        if self._audit_db:
            self._audit_db.close()
            print("Closing audits db")
        if self._state_db:
            self._state_db.close()
            print("Closing audits db")


data_stores = DataStores()