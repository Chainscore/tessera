from jam.storage.db.kv import KVStore

class Settings:
    # Node settings
    NODE_NAME: str = "JAM-Node"
    NODE_ID: str | None = None

    # Network settings
    LISTEN_ADDRESS: str = "0.0.0.0"
    LISTEN_PORT: int = 30333

    # Database settings
    DB_PATH: str = "data/db"
    AUDIT_DB_PATH: str = "data/audit"

    ENV_PREFIX = "JAM_"
    ENV_FILE = ".env"

    @property
    def db(self):
        return KVStore(self.DB_PATH)
    
    @property
    def audit_db(self):
        return KVStore(self.AUDIT_DB_PATH)

settings: Settings | None = None

def setup_setting(name: str, port: int,  db_path = "data/db", node_id = None):
    global settings
    s = Settings()
    s.NODE_NAME = name
    s.LISTEN_PORT = port
    s.DB_PATH = db_path
    s.AUDIT_DB_PATH = db_path + "/audit"
    s.NODE_ID = node_id
    settings = s
