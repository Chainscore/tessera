from contextlib import contextmanager
from jam.storage.db.kv import KVStore

@contextmanager
def open_database(path):
    """
    Context manager for opening a KVStore database

    Args:
        path (str): The path to the database file


    Yields:
        KVStore: The database

    Example:
        >>> with open_database("db/state.db") as db:
        >>>     db.put("key", "value")
        >>>     value = db.get("key")
    """
    db = KVStore(path)
    try:
        yield db
    finally:
        db.close()