import pytest
from jam.types.base.bit import Bit
from jam.utils.jstruct.serde import JsonDeserializationError


def test_bit_json_serialization():
    # Test bit 0
    bit_zero = Bit(0)
    json_zero = bit_zero.to_json()
    assert json_zero == 0
    assert Bit.from_json(json_zero) == bit_zero

    # Test bit 1
    bit_one = Bit(1)
    json_one = bit_one.to_json()
    assert json_one == 1
    assert Bit.from_json(json_one) == bit_one


def test_bit_json_invalid_input():
    # Test with invalid numeric values
    with pytest.raises(JsonDeserializationError):
        Bit.from_json(2)  # Only 0 and 1 are valid

    with pytest.raises(JsonDeserializationError):
        Bit.from_json(-1)  # Negative values are invalid

    # Test with invalid types
    with pytest.raises(JsonDeserializationError):
        Bit.from_json("0")  # String instead of int

    with pytest.raises(JsonDeserializationError):
        Bit.from_json(None)  # None instead of int

    with pytest.raises(JsonDeserializationError):
        Bit.from_json([])  # List instead of int

    with pytest.raises(JsonDeserializationError):
        Bit.from_json({})  # Dict instead of int


def test_bit_json_roundtrip():
    # Test roundtrip for bit 0
    original_zero = Bit(0)
    json_data = original_zero.to_json()
    reconstructed = Bit.from_json(json_data)
    assert reconstructed == original_zero
    assert isinstance(reconstructed, Bit)
    assert int(reconstructed) == 0

    # Test roundtrip for bit 1
    original_one = Bit(1)
    json_data = original_one.to_json()
    reconstructed = Bit.from_json(json_data)
    assert reconstructed == original_one
    assert isinstance(reconstructed, Bit)
    assert int(reconstructed) == 1


def test_bit_json_comparison():
    # Test equality after serialization/deserialization
    bit = Bit(0)
    json_data = bit.to_json()
    reconstructed = Bit.from_json(json_data)

    assert reconstructed == bit
    assert hash(reconstructed) == hash(bit)
    assert bool(reconstructed) == bool(bit)
    assert int(reconstructed) == int(bit)
    assert bytes(reconstructed) == bytes(bit)

    # Test comparison operators
    bit_zero = Bit.from_json(0)
    bit_one = Bit.from_json(1)

    assert bit_zero < bit_one
    assert bit_one > bit_zero
    assert bit_zero <= bit_one
    assert bit_one >= bit_zero
    assert bit_zero != bit_one


def test_bit_json_operations():
    # Test bitwise operations after deserialization
    bit_zero = Bit.from_json(0)
    bit_one = Bit.from_json(1)

    # Test AND operation
    assert (bit_zero & bit_zero) == Bit(0)
    assert (bit_zero & bit_one) == Bit(0)
    assert (bit_one & bit_zero) == Bit(0)
    assert (bit_one & bit_one) == Bit(1)

    # Test boolean conversion
    assert bool(bit_zero) is False
    assert bool(bit_one) is True

    # Test integer conversion
    assert int(bit_zero) == 0
    assert int(bit_one) == 1
