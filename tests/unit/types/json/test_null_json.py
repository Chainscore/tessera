import pytest
from jam.types.base.null import Null, Nullable

def test_null_json_serialization():
    # Test Null singleton
    json_null = Null.to_json()
    assert json_null is None
    assert Nullable.from_json(json_null) == Null
    
    # Test new Nullable instance
    nullable = Nullable()
    json_nullable = nullable.to_json()
    assert json_nullable is None
    assert Nullable.from_json(json_nullable) == Null
    assert Nullable.from_json(json_nullable) == nullable

def test_null_json_invalid_input():
    # Test with invalid input types
    with pytest.raises(ValueError):
        Nullable.from_json("null")  # String instead of None

    with pytest.raises(ValueError):
        Nullable.from_json(0)  # Integer instead of None

    with pytest.raises(ValueError):
        Nullable.from_json(False)  # Boolean instead of None

    with pytest.raises(ValueError):
        Nullable.from_json([])  # Empty list instead of None

def test_null_json_roundtrip():
    # Test roundtrip with Null singleton
    original = Null
    json_data = original.to_json()
    reconstructed = Nullable.from_json(json_data)
    assert original == reconstructed
    assert isinstance(reconstructed, Nullable)
    assert reconstructed.get() is None

    # Test roundtrip with new Nullable instance
    original = Nullable()
    json_data = original.to_json()
    reconstructed = Nullable.from_json(json_data)
    assert original == reconstructed
    assert isinstance(reconstructed, Nullable)
    assert reconstructed.get() is None

def test_null_singleton_behavior():
    # Verify that all Nullable instances are equal
    null1 = Nullable()
    null2 = Nullable()
    assert null1 == null2
    assert null1 == Null
    assert null2 == Null

    # Verify JSON serialization produces same result
    assert null1.to_json() == null2.to_json() == Null.to_json()

    # Verify deserialization always returns the singleton
    json_data = None
    assert Nullable.from_json(json_data) == Null
    assert Nullable.from_json(json_data) == Nullable.from_json(json_data)