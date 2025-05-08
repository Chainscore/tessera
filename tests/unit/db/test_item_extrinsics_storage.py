import pytest
from unittest.mock import MagicMock, patch
from jam.db.kv import KVStore
from jam.storage.item_extrinsics import ItemExtrinsics
from jam.types.protocol.crypto import Hash
from jam.types.work.package import WorkPackage
from jam.types.base.sequences.bytes.bytes import Bytes


def test_ext_encode(db_path):
    """Test encoiding extrinsic data."""
    db = KVStore(db_path)
    test_data = [[b'12345']]
    ext_data, specs = ItemExtrinsics.encode(test_data)

    mock_item = MagicMock()
    mock_item.extrinsic = specs

    mock_package = MagicMock(spec=WorkPackage)
    mock_package.items = [mock_item]

    ItemExtrinsics.store(mock_package, ext_data, db)


def test_store_extrinsics(db_path):
    """Test storing extrinsic data."""
    db = KVStore(db_path)
    # Create test data bytes
    test_data = b'12345'
    # Create test wp
    mock_extrinsic = MagicMock()
    mock_extrinsic.len = 5
    mock_extrinsic.hash = Hash.blake2b(test_data)

    mock_item = MagicMock()
    mock_item.extrinsic = [mock_extrinsic]

    mock_package = MagicMock(spec=WorkPackage)
    mock_package.items = [mock_item]

    ItemExtrinsics.store(mock_package, [test_data], db)

    db_data = db.get(bytes(mock_extrinsic.hash))
    assert db_data is not None
    assert db_data == test_data

def test_store_invalid_hash(db_path):
    """Test that storing with invalid hash raises an error."""
    db = KVStore(db_path)
    # Create test data
    test_data = b'12345'

    # Use different data hash to trigger error
    wrong_data = b'wrong'

    mock_extrinsic = MagicMock()
    mock_extrinsic.len = 5
    mock_extrinsic.hash = Hash.blake2b(wrong_data)

    mock_item = MagicMock()
    mock_item.extrinsic = [mock_extrinsic]

    mock_package = MagicMock(spec=WorkPackage)
    mock_package.items = [mock_item]

    # Should raise ValueError due to hash mismatch
    with pytest.raises(ValueError, match="Invalid WP: Extrinsic data mismatch"):
        ItemExtrinsics.store(mock_package, [test_data], db)

    # Verify nothing was stored
    assert db.get(bytes(mock_extrinsic.hash)) is None


def test_get_extrinsic(db_path):
    """Test retrieving stored extrinsic data."""
    db = KVStore(db_path)

    # Store some test data first
    test_data = b'extrinsic_test_data'
    hash_value = Hash.blake2b(test_data)
    hash_bytes = bytes(hash_value)

    # Store directly in the database
    db.put(hash_bytes, test_data)

    # Use the get method to retrieve it - make sure we're using the same hash format
    result = ItemExtrinsics.get(extrinsic_hash=hash_bytes, db=db)

    # Verify the data matches
    assert result == test_data

    # Clean up
    db.close()


def test_multiple_extrinsics(db_path):
    """Test storing multiple extrinsics in one package."""
    db = KVStore(db_path)

    # Create test data for multiple extrinsics
    test_data1 = b'123'
    test_data2 = b'4567'
    combined_data = [test_data1 + test_data2]

    # Create mock extrinsics with proper lengths and hashes
    mock_extrinsic1 = MagicMock()
    mock_extrinsic1.len = len(test_data1)
    mock_extrinsic1.hash = Hash.blake2b(test_data1)

    mock_extrinsic2 = MagicMock()
    mock_extrinsic2.len = len(test_data2)
    mock_extrinsic2.hash = Hash.blake2b(test_data2)

    # Create mock item with both extrinsics
    mock_item = MagicMock()
    mock_item.extrinsic = [mock_extrinsic1, mock_extrinsic2]

    # Create mock package
    mock_package = MagicMock(spec=WorkPackage)
    mock_package.items = [mock_item]

    # Store extrinsics - pass byte string directly instead of Bytes object
    ItemExtrinsics.store(mock_package, combined_data, db)

    # Verify both extrinsics were stored correctly
    assert db.get(bytes(mock_extrinsic1.hash)) == test_data1
    assert db.get(bytes(mock_extrinsic2.hash)) == test_data2

    # Clean up
    db.close()
