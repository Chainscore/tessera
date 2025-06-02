import os

from jam.config.settings import settings
from jam.storage.db.kv import KVStore

os.makedirs(settings.DB_PATH, exist_ok=True)
os.makedirs(settings.D3L_PATH, exist_ok=True)
os.makedirs(settings.AUDIT_DB_PATH, exist_ok=True)

main_db = KVStore(settings.DB_PATH)
d3l_db = KVStore(settings.D3L_PATH)
audits_db = KVStore(settings.AUDIT_DB_PATH)

def configure_db_paths():
    global main_db, audits_db, d3l_db
    shutdown()

    os.makedirs(settings.DB_PATH, exist_ok=True)
    os.makedirs(settings.D3L_PATH, exist_ok=True)
    os.makedirs(settings.AUDIT_DB_PATH, exist_ok=True)

    main_db = KVStore(settings.DB_PATH)
    d3l_db = KVStore(settings.D3L_PATH)
    audits_db = KVStore(settings.AUDIT_DB_PATH)

def shutdown():
    main_db.close()
    d3l_db.close()
    audits_db.close()