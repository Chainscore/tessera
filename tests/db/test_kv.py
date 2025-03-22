import pytest
import os
import shutil
import tempfile
from jam.db.kv import KVStore

@pytest.fixture
def db_path():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_kv_store_basic_operations(db_path):
    """Test basic operations of KVStore."""
    # Initialize store
    kv = KVStore(db_path)
    
    # Test put and get
    kv.put("key1", "value1")
    assert kv.get("key1") == "value1"
    
    # Test overwrite
    kv.put("key1", "updated_value")
    assert kv.get("key1") == "updated_value"
    
    # Test get non-existent key
    assert kv.get("non_existent_key") is None
    
    # Test delete
    kv.delete("key1")
    assert kv.get("key1") is None
    
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
        kv.put(key, value)
    
    # Verify all values
    for key, expected_value in test_data.items():
        assert kv.get(key) == expected_value
    
    # Delete some items
    kv.delete("user:2")
    assert kv.get("user:2") is None
    assert kv.get("user:1") == "John Doe"  # Other keys still exist
    
    kv.close()

def test_kv_store_reopen(db_path):
    """Test that data persists after closing and reopening."""
    # Create and populate store
    kv = KVStore(db_path)
    kv.put("persistent_key", "persistent_value")
    kv.close()
    
    # Reopen and check data
    kv2 = KVStore(db_path)
    assert kv2.get("persistent_key") == "persistent_value"
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
        kv.put(key, value)
    
    for key, expected_value in unicode_test.items():
        assert kv.get(key) == expected_value
    
    kv.close() 