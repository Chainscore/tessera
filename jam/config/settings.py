from jam.storage.db.kv import KVStore

class Settings:
    # Node settings
    NODE_NAME: str = "JAM-Node"
    NODE_ID: str | None = None

    # Network settings
    LISTEN_ADDRESS: str = "0.0.0.0"
    LISTEN_PORT: int = 30333
    MAX_PEERS: int = 50

    # Database settings
    NODE_PATH = f"db/{LISTEN_PORT}"
    DB_PATH = f"{NODE_PATH}/node"
    D3L_PATH = f"{NODE_PATH}/d3l"

    ENV_PREFIX = "JAM_"
    ENV_FILE = ".env"

    @property
    def db(self):
        return KVStore(self.DB_PATH)

    @property
    def d3l(self):
        return KVStore(self.D3L_PATH)

settings: Settings = Settings()

def setup_setting(name: str, port: int,  db_path = "data/db", node_id = None):
    global settings
    s = Settings()
    s.NODE_NAME = name
    s.LISTEN_PORT = port
    s.DB_PATH = db_path
    s.AUDIT_DB_PATH = db_path + "/audit"
    s.NODE_ID = node_id
    settings = s
