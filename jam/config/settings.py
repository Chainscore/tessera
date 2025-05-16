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
    NODE_PATH = f"data/{LISTEN_PORT}"
    DB_PATH = f"{NODE_PATH}/main"
    D3L_PATH = f"{NODE_PATH}/d3l"
    AUDIT_DB_PATH = f"{NODE_PATH}/audit"

    ENV_PREFIX = "JAM_"
    ENV_FILE = ".env"

    @property
    def db(self):
        return KVStore(self.DB_PATH)

    @property
    def d3l(self):
        return KVStore(self.D3L_PATH)

    @property
    def audit(self):
        return KVStore(self.AUDIT_DB_PATH)

settings: Settings = Settings()

def setup_setting(name: str, port: int,  db_path = "data", node_id = None):
    global settings
    s = Settings()

    node_path = f"{db_path}/{port}"
    settings.NODE_PATH = node_path

    settings.NODE_NAME = name
    settings.LISTEN_PORT = port
    settings.DB_PATH = f"{node_path}/main"
    settings.AUDIT_DB_PATH = f"{node_path}/audit"
    settings.D3L_PATH = f"{node_path}/d3l"
    settings.NODE_ID = node_id
   # settings = s

    print("settings updated to", settings)
