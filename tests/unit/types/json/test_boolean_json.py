import pytest
from jam.types.base.boolean import Boolean
from jam.utils.json.serde import JsonDeserializationError

def test_boolean_json_serialization():
    # Test True value
    b_true = Boolean(True)
    json_true = b_true.to_json()
    assert json_true is True
    assert Boolean.from_json(json_true) == b_true
    
    # Test False value
    b_false = Boolean(False)
    json_false = b_false.to_json()
    assert json_false is False
    assert Boolean.from_json(json_false) == b_false

def test_boolean_json_invalid_input():
    # Test with invalid input types
    with pytest.raises(JsonDeserializationError):
        Boolean.from_json("true")  # String instead of bool
    
    with pytest.raises(JsonDeserializationError):
        Boolean.from_json(1)  # Integer instead of bool
    
    with pytest.raises(JsonDeserializationError):
        Boolean.from_json(None)  # None instead of bool

def test_boolean_json_roundtrip():
    # Test roundtrip serialization
    original = Boolean(True)
    json_data = original.to_json()
    reconstructed = Boolean.from_json(json_data)
    assert original == reconstructed
    assert isinstance(reconstructed, Boolean)
    
    # Test roundtrip with False
    original = Boolean(False)
    json_data = original.to_json()
    reconstructed = Boolean.from_json(json_data)
    assert original == reconstructed
    assert isinstance(reconstructed, Boolean) 