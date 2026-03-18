import json

import pytest
from rockstore import RockStore

pytestmark = pytest.mark.unit


def test_kv_store_basic_operations(db_path):
    """Test basic operations of RockStore."""
    kv = RockStore(db_path)

    # Test put and get
    kv.put("State".encode(), "StateValue".encode())
    kv.put("ServiceId".encode(), json.dumps(["PreImageKey1", "PreImageKey2"]).encode())
    value = kv.get("ServiceId".encode())
    valueList = json.loads(value)
    assert valueList == ["PreImageKey1", "PreImageKey2"]
    assert kv.get("State".encode()) == "StateValue".encode()

    # Test overwrite
    kv.put("key1".encode(), "updated_value".encode())
    assert kv.get("key1".encode()) == "updated_value".encode()

    # Test get non-existent key
    assert kv.get("non_existent_key".encode()) is None

    # Test delete
    kv.delete("key1".encode())
    assert kv.get("key1".encode()) is None

    kv.close()


def test_kv_store_multiple_operations(db_path):
    """Test multiple operations on RockStore."""
    kv = RockStore(db_path)

    test_data = {
        "user:1": "John Doe",
        "user:2": "Jane Smith",
        "user:3": "Bob Johnson",
    }

    for key, value in test_data.items():
        kv.put(key.encode(), value.encode())

    for key, expected_value in test_data.items():
        assert kv.get(key.encode()) == expected_value.encode()

    kv.delete("user:2".encode())
    assert kv.get("user:2".encode()) is None
    assert kv.get("user:1".encode()) == "John Doe".encode()

    kv.close()


def test_kv_store_reopen(db_path):
    """Test that data persists after closing and reopening."""
    kv = RockStore(db_path)
    kv.put("persistent_key".encode(), "persistent_value".encode())
    kv.close()

    kv2 = RockStore(db_path)
    assert kv2.get("persistent_key".encode()) == "persistent_value".encode()
    kv2.close()


def test_unicode_strings(db_path):
    """Test handling of Unicode strings."""
    kv = RockStore(db_path)

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
