import pytest
from jam.types.base.choices.option import Option, decodable_option
from jam.types.base.string import String
from jam.types.base.integers.fixed import I64
from jam.types.base.boolean import Boolean
from jam.types.base.null import Null, Nullable
from jam.utils.json.serde import JsonDeserializationError


@decodable_option(String)
class StringOption(Option):
    pass


@decodable_option(I64)
class IntOption(Option):
    pass


@decodable_option(Boolean)
class BoolOption(Option):
    pass


def test_option_json_serialization_none():
    # Test None value for different option types
    string_none = StringOption(Null)
    assert string_none.to_json() is None
    assert StringOption.from_json(None) == string_none

    int_none = IntOption(Null)
    assert int_none.to_json() is None
    assert IntOption.from_json(None) == int_none

    bool_none = BoolOption(Null)
    assert bool_none.to_json() is None
    assert BoolOption.from_json(None) == bool_none


def test_option_json_serialization_some():
    # Test Some value for string option
    string_some = StringOption(String("test"))
    json_str = string_some.to_json()
    assert json_str == "test"
    assert StringOption.from_json(json_str) == string_some

    # Test Some value for int option
    int_some = IntOption(I64(42))
    json_int = int_some.to_json()
    assert json_int == 42
    assert IntOption.from_json(json_int) == int_some

    # Test Some value for bool option
    bool_some = BoolOption(Boolean(True))
    json_bool = bool_some.to_json()
    assert json_bool is True
    assert BoolOption.from_json(json_bool) == bool_some


def test_option_json_invalid_input():
    # Test with invalid types for string option
    with pytest.raises(JsonDeserializationError):
        StringOption.from_json(42)  # Int instead of str

    with pytest.raises(JsonDeserializationError):
        StringOption.from_json(True)  # Bool instead of str

    # Test with invalid types for int option
    with pytest.raises(JsonDeserializationError):
        IntOption.from_json("42")  # String instead of int

    # Test with invalid types for bool option
    with pytest.raises(JsonDeserializationError):
        BoolOption.from_json("true")  # String instead of bool

    with pytest.raises(JsonDeserializationError):
        BoolOption.from_json(1)  # Int instead of bool


def test_option_json_roundtrip():
    # Test roundtrip for None values
    test_none_cases = [StringOption(Null), IntOption(Null), BoolOption(Null)]

    for original in test_none_cases:
        json_data = original.to_json()
        assert json_data is None
        reconstructed = original.__class__.from_json(
            json_data,
        )
        assert reconstructed == original
        assert isinstance(list(reconstructed.value.values())[0], Nullable)

    # Test roundtrip for Some values
    test_some_cases = [
        (StringOption(String("test")), "test"),
        (IntOption(I64(42)), 42),
        (BoolOption(Boolean(True)), True),
    ]

    for original, expected_json in test_some_cases:
        json_data = original.to_json()
        assert json_data == expected_json
        reconstructed = original.__class__.from_json(
            json_data,
        )
        assert reconstructed == original
        assert not isinstance(reconstructed.value, Nullable)


def test_option_json_special_values():
    # Test string option with special characters
    special_chars = StringOption(String("Hello\n\t世界"))
    json_data = special_chars.to_json()
    assert json_data == "Hello\n\t世界"
    assert StringOption.from_json(json_data) == special_chars

    # Test string option with emoji
    emoji = StringOption(String("Hello 👋"))
    json_data = emoji.to_json()
    assert json_data == "Hello 👋"
    assert StringOption.from_json(json_data) == emoji

    # Test int option with boundary values
    max_int = IntOption(I64(2**31 - 1))
    json_data = max_int.to_json()
    assert json_data == 2**31 - 1
    assert IntOption.from_json(json_data) == max_int

    min_int = IntOption(I64(-(2**31)))
    json_data = min_int.to_json()
    assert json_data == -(2**31)
    assert IntOption.from_json(json_data) == min_int


def test_option_json_comparison():
    # Test equality after serialization/deserialization
    some_string = StringOption(String("test"))
    json_data = some_string.to_json()
    reconstructed = StringOption.from_json(json_data)
    assert reconstructed == some_string

    none_string = StringOption(Null)
    json_data = none_string.to_json()
    reconstructed = StringOption.from_json(json_data)
    assert reconstructed == none_string

    # Test that None values are equal regardless of option type
    assert StringOption(Null).to_json() == IntOption(Null).to_json()
    assert StringOption.from_json(None) == StringOption(Null)
    assert IntOption.from_json(None) == IntOption(Null)
    assert BoolOption.from_json(None) == BoolOption(Null)
