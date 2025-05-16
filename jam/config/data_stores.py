import os

from jam.config.settings import settings
from jam.storage.db.kv import KVStore

os.makedirs(settings.DB_PATH, exist_ok=True)
os.makedirs(settings.D3L_PATH, exist_ok=True)
os.makedirs(settings.AUDIT_DB_PATH, exist_ok=True)
main_db = KVStore(settings.DB_PATH)
audit_da = KVStore(settings.AUDIT_DB_PATH)
d3l = KVStore(settings.D3L_PATH)

def configure_db_paths(parent_path = "data", port = 30333):
    global main_db, audit_da, d3l
    node_path = f"{parent_path}/{port}"
    main_db = KVStore(parent_path+"/main")
    audit_da = KVStore(parent_path+"/audit")
    d3l = KVStore(parent_path+"/d3l")
