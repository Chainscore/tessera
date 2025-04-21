from jam.db.kv import KVStore
from jam.storage.queue import StorageQueue

def test_storage_queue(db_path):
    db = KVStore(db_path)
    queue = StorageQueue("test")
    queue.push(db, b"test1")
    queue.push(db, b"test2")
    queue.push(db, b"test3")
    # test metadata
    metadata = queue.metadata(db)
    assert int(metadata.head) == 0
    assert int(metadata.tail) == 3
    assert int(metadata.count) == 3

    assert queue.pop(db) == b"test1"
    assert queue.pop(db) == b"test2"
    assert queue.pop(db) == b"test3"
    assert queue.pop(db) is None

def test_storage_queue_get(db_path):
    db = KVStore(db_path)
    queue = StorageQueue("test")
    queue.push(db, b"test1")
    queue.push(db, b"test2")
    queue.push(db, b"test3")
    
    assert queue.get(db, 1, 0) == [b"test1"]
    assert queue.get(db, 1, 1) == [b"test2"]
    assert queue.get(db, 1, 2) == [b"test3"]
    assert queue.get(db, 1, 3) == []
    
    # Get multiple items
    assert queue.get(db, 2, 0) == [b"test1", b"test2"]
    assert queue.get(db, 2, 1) == [b"test2", b"test3"]
    assert queue.get(db, 2, 2) == [b"test3"]
    assert queue.get(db, 2, 3) == []


def test_storage_queue_pop(db_path):
    db = KVStore(db_path)
    queue = StorageQueue("test")
    queue.push(db, b"test1")
    queue.push(db, b"test2")
    queue.push(db, b"test3")

    assert queue.pop(db) == b"test1"
    metadata = queue.metadata(db)
    assert int(metadata.head) == 1
    assert int(metadata.tail) == 3
    assert int(metadata.count) == 2
    assert queue.pop(db) == b"test2"
    metadata = queue.metadata(db)
    assert int(metadata.head) == 2
    assert int(metadata.tail) == 3
    assert int(metadata.count) == 1
    assert queue.pop(db) == b"test3"
    metadata = queue.metadata(db)
    assert int(metadata.head) == 3
    assert int(metadata.tail) == 3
    assert int(metadata.count) == 0

# Remove items in between and test pop
def test_storage_queue_pop_in_between(db_path):
    db = KVStore(db_path)
    queue = StorageQueue("test")
    queue.push(db, b"test1")
    queue.push(db, b"test2")
    queue.push(db, b"test3")
    queue.remove_value(db, b"test2")
    assert queue.pop(db) == b"test1"
    assert queue.pop(db) == b"test3"
    assert queue.pop(db) is None