from jam.db.kv import KVStore

main_db = KVStore("data")
audit_da = KVStore("data/audit")
d3l = KVStore("data/d3l")

def configure_db_paths(parent_path = "data"):
    global main_db, audit_da, d3l
    main_db = KVStore(parent_path)
    audit_da = KVStore(parent_path+"audit")
    d3l = KVStore(parent_path+"d3l")
