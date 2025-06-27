class Settings:
    # Node settings
    NODE_NAME: str = "JAM-Node"
    NODE_ID: str | None = None

    # Network settings
    LISTEN_ADDRESS: str = "127.0.0.1"
    LISTEN_PORT: int = 40000
    MAX_PEERS: int = 50

    # Database settings
    NODE_PATH = f"data/{LISTEN_PORT}"
    DB_PATH = f"{NODE_PATH}/main"
    D3L_PATH = f"{NODE_PATH}/d3l"
    AUDIT_DB_PATH = f"{NODE_PATH}/audit"
    STATE_DB_PATH = f"{NODE_PATH}/state"

    ENV_PREFIX = "JAM_"
    ENV_FILE = "40000.env"

    @property
    def db(self):
        from jam.config.data_stores import data_stores
        return data_stores.main_db

    @property
    def d3l(self):
        from jam.config.data_stores import data_stores
        return data_stores.d3l

    @property
    def audit(self):
        from jam.config.data_stores import data_stores
        return data_stores.audit_da

    @property
    def state_db(self):
        from jam.config.data_stores import data_stores
        return data_stores.state_db

settings: Settings = Settings()

def setup_setting(name: str, port: int,  db_path = "data", node_id = None) -> Settings:
    global settings

    node_path = f"{db_path}/{port}"
    settings.NODE_PATH = node_path

    settings.NODE_NAME = name
    settings.LISTEN_PORT = port
    settings.DB_PATH = f"{node_path}/main"
    settings.AUDIT_DB_PATH = f"{node_path}/audit"
    settings.STATE_DB_PATH = f"{node_path}/state"
    settings.D3L_PATH = f"{node_path}/d3l"
    settings.NODE_ID = node_id
    settings.ENV_FILE = f"{port}.env"


    # Reconfigure DBS
    from jam.config.data_stores import data_stores
    data_stores.configure_db_paths()

    return settings