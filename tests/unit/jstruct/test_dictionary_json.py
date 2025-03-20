import pytest
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.string import String
from jam.types.base.integers.fixed import I32 as Int32
from jam.types.base.boolean import Boolean
from jam.utils.jstruct.serde import JsonDeserializationError


@decodable_dictionary(String, Int32)
class StringIntDict(Dictionary[String, Int32]):
    pass


@decodable_dictionary(String, String)
class StringStringDict(Dictionary[String, String]):
    pass


@decodable_dictionary(String, Boolean)
class StringBoolDict(Dictionary[String, Boolean]):
    pass


def test_dictionary_json_serialization_string_int():
    # Create a dictionary with string keys and integer values
    d = StringIntDict(
        {String("one"): Int32(1), String("two"): Int32(2), String("three"): Int32(3)}
    )

    json_dict = d.to_json()
    assert isinstance(json_dict, dict)
    assert json_dict == {"one": 1, "two": 2, "three": 3}

    # Test deserialization
    reconstructed = StringIntDict.from_json(json_dict)
    assert reconstructed == d


def test_dictionary_json_serialization_string_string():
    # Create a dictionary with string keys and string values
    d = StringStringDict(
        {
            String("hello"): String("world"),
            String("foo"): String("bar"),
            String("test"): String("value"),
        }
    )

    json_dict = d.to_json()
    assert isinstance(json_dict, dict)
    assert json_dict == {"hello": "world", "foo": "bar", "test": "value"}

    # Test deserialization
    reconstructed = StringStringDict.from_json(json_dict)
    assert reconstructed == d


def test_dictionary_json_serialization_string_bool():
    # Create a dictionary with string keys and boolean values
    d = StringBoolDict(
        {
            String("is_valid"): Boolean(True),
            String("is_active"): Boolean(False),
            String("is_enabled"): Boolean(True),
        }
    )

    json_dict = d.to_json()
    assert isinstance(json_dict, dict)
    assert json_dict == {"is_valid": True, "is_active": False, "is_enabled": True}

    # Test deserialization
    reconstructed = StringBoolDict.from_json(json_dict)
    assert reconstructed == d


def test_dictionary_json_empty():
    # Test empty dictionary
    d = StringIntDict()
    json_dict = d.to_json()
    assert isinstance(json_dict, dict)
    assert json_dict == {}

    reconstructed = StringIntDict.from_json(json_dict)
    assert reconstructed == d


def test_dictionary_json_invalid_input():
    # Test with invalid input types
    with pytest.raises(ValueError):
        StringIntDict.from_json([])  # List instead of dict

    with pytest.raises(ValueError):
        StringIntDict.from_json(None)  # None instead of dict

    with pytest.raises(ValueError):
        StringIntDict.from_json("not a dict")  # String instead of dict

    # Test with invalid value types
    with pytest.raises(JsonDeserializationError):
        StringIntDict.from_json({"key": "not an int"})  # String instead of int


def test_dictionary_json_nested():
    # Create nested dictionaries
    inner = StringStringDict({String("inner_key"): String("inner_value")})

    @decodable_dictionary(String, StringStringDict)
    class NestedDict(Dictionary[String, StringStringDict]):
        pass

    outer = NestedDict({String("outer_key"): inner})

    json_dict = outer.to_json()
    assert isinstance(json_dict, dict)
    assert json_dict == {"outer_key": {"inner_key": "inner_value"}}

    # Test deserialization of nested structure
    reconstructed = NestedDict.from_json(json_dict)
    assert reconstructed == outer


def test_dictionary_json_special_values():
    # Test dictionary with special string values
    d = StringStringDict(
        {
            String("unicode"): String("Hello 世界"),
            String("emoji"): String("👋 🌍"),
            String("special"): String("Line1\nLine2\tTabbed"),
        }
    )

    json_dict = d.to_json()
    assert isinstance(json_dict, dict)
    assert json_dict == {
        "unicode": "Hello 世界",
        "emoji": "👋 🌍",
        "special": "Line1\nLine2\tTabbed",
    }

    reconstructed = StringStringDict.from_json(json_dict)
    assert reconstructed == d
