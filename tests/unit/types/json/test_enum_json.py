import pytest
from jam.types.base.enum import Enum, decodable_enum
from jam.utils.json.serde import JsonDeserializationError

@decodable_enum
class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

@decodable_enum
class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

@decodable_enum
class EmptyEnum(Enum):
    pass

def test_enum_json_serialization_by_name():
    # Test serialization using enum names
    assert Color.RED.to_json() == 1
    assert Color.GREEN.to_json() == 2
    assert Color.BLUE.to_json() == 3
    
    # Test deserialization using enum names
    assert Color.from_json("RED") == Color.RED
    assert Color.from_json("GREEN") == Color.GREEN
    assert Color.from_json("BLUE") == Color.BLUE

def test_enum_json_serialization_by_value():
    # Test deserialization using enum values
    assert Color.from_json(1) == Color.RED
    assert Color.from_json(2) == Color.GREEN
    assert Color.from_json(3) == Color.BLUE
    
    # Test with string values
    assert Status.from_json("active") == Status.ACTIVE
    assert Status.from_json("inactive") == Status.INACTIVE
    assert Status.from_json("pending") == Status.PENDING

def test_enum_json_invalid_input():
    # Test with invalid names
    with pytest.raises(JsonDeserializationError):
        Color.from_json("YELLOW")  # Non-existent enum name
    
    with pytest.raises(JsonDeserializationError):
        Color.from_json(4)  # Non-existent enum value
    
    with pytest.raises(JsonDeserializationError):
        Status.from_json("completed")  # Non-existent status
    
    # Test with invalid types
    with pytest.raises(JsonDeserializationError):
        Color.from_json(None)
    
    with pytest.raises(JsonDeserializationError):
        Color.from_json([])
    
    with pytest.raises(JsonDeserializationError):
        Color.from_json({})

def test_enum_json_roundtrip():
    # Test roundtrip for numeric enum values
    for color in Color:
        json_data = color.to_json()
        reconstructed = Color.from_json(color.name)
        assert reconstructed == color
        assert isinstance(reconstructed, Color)
    
    # Test roundtrip for string enum values
    for status in Status:
        json_data = status.to_json()
        reconstructed = Status.from_json(json_data)
        assert reconstructed == status
        assert isinstance(reconstructed, Status)

def test_enum_json_comparison():
    # Test equality after serialization/deserialization
    color = Color.RED
    json_data = color.to_json()
    reconstructed = Color.from_json(json_data)
    
    assert reconstructed == color
    assert reconstructed is color  # Should be same instance
    assert hash(reconstructed) == hash(color)
    
    # Test with string-based enum
    status = Status.ACTIVE
    json_data = status.to_json()
    reconstructed = Status.from_json(json_data)
    
    assert reconstructed == status
    assert reconstructed is status  # Should be same instance
    assert hash(reconstructed) == hash(status)

def test_enum_json_empty():
    # Test empty enum behavior
    with pytest.raises(JsonDeserializationError):
        EmptyEnum.from_json("anything")
    
    with pytest.raises(JsonDeserializationError):
        EmptyEnum.from_json(1)

def test_enum_json_case_sensitivity():
    # Test case sensitivity in name-based deserialization
    with pytest.raises(JsonDeserializationError):
        Color.from_json("red")  # Should be "RED"
    
    with pytest.raises(JsonDeserializationError):
        Status.from_json("ACTive")  # Should be "active"

def test_enum_json_type_coercion():
    # Test that values are not type-coerced
    with pytest.raises(JsonDeserializationError):
        Color.from_json("1")  # String version of numeric value
    
    with pytest.raises(JsonDeserializationError):
        Status.from_json(1)  # Numeric version of string value 