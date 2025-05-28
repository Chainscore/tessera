from jam.storage.db.kv import KVStore
import json
from jam.state.ghost import GhostState as State


def test_kv_store_basic_operations(db_path):
    """Test basic operations of KVStore."""
    # Initialize store
    kv = KVStore(db_path)
    
    # Test put and get
    kv.put("State".encode(), "StateValue".encode())
    kv.put("ServiceId".encode(), json.dumps(["PreImageKey1", "PreImageKey2"]).encode())
    value=kv.get("ServiceId".encode())
    valueList=json.loads(value)
    assert valueList==["PreImageKey1", "PreImageKey2"]
    assert kv.get("State".encode()) == "StateValue".encode()
    
    # State checking
    state = State.genesis()
    state.save(kv)
    
    
    # Test overwrite
    kv.put("key1".encode(), "updated_value".encode())
    assert kv.get("key1".encode()) == "updated_value".encode()
    
    # Test get non-existent key
    assert kv.get("non_existent_key".encode()) is None
    
    # Test delete
    kv.delete("key1".encode())
    assert kv.get("key1".encode()) is None

    # Close the store
    kv.close()

def test_kv_store_multiple_operations(db_path):
    """Test multiple operations on KVStore."""
    kv = KVStore(db_path)
    
    # Add multiple key-value pairs
    test_data = {
        "user:1": "John Doe",
        "user:2": "Jane Smith",
        "user:3": "Bob Johnson",
    }
    
    for key, value in test_data.items():
        kv.put(key.encode(), value.encode())
    
    # Verify all values
    for key, expected_value in test_data.items():
        assert kv.get(key.encode()) == expected_value.encode()
    
    # Delete some items
    kv.delete("user:2".encode())
    assert kv.get("user:2".encode()) is None
    assert kv.get("user:1".encode()) == "John Doe".encode()  # Other keys still exist
    
    kv.close()

def test_kv_store_reopen(db_path):
    """Test that data persists after closing and reopening."""
    # Create and populate store
    kv = KVStore(db_path)
    kv.put("persistent_key".encode(), "persistent_value".encode())
    kv.close()
    
    # Reopen and check data
    kv2 = KVStore(db_path)
    assert kv2.get("persistent_key".encode()) == "persistent_value".encode()
    kv2.close()

def test_unicode_strings(db_path):
    """Test handling of Unicode strings."""
    kv = KVStore(db_path)
    
    # Various Unicode characters
    unicode_test = {
        "emoji": "😀🌍🚀",
        "chinese": "你好，世界",
        "arabic": "مرحبا بالعالم",
        "russian": "Привет, мир",
    }
    
    for key, value in unicode_test.items():
        kv.put(key.encode(), value.encode())
    
    for key, expected_value in unicode_test.items():
        assert kv.get(key.encode()) == expected_value.encode()
    
    kv.close() 


