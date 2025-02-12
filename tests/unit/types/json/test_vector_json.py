import pytest
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.base.string import String
from jam.types.base.integers.fixed import U32
from jam.types.base.boolean import Boolean
from jam.utils.json.serde import JsonDeserializationError


@decodable_vector(String)
class StringVector(Vector[String]):
    pass


@decodable_vector(U32)
class IntVector(Vector[U32]):
    pass


@decodable_vector(Boolean)
class BoolVector(Vector[Boolean]):
    pass


def test_vector_json_serialization_strings():
    # Test vector of strings
    strings = [String("hello"), String("world"), String("test")]
    v = StringVector(strings)

    json_data = v.to_json()
    assert isinstance(json_data, list)
    assert json_data == ["hello", "world", "test"]

    # Test deserialization
    reconstructed = StringVector.from_json(json_data)
    assert reconstructed == v
    assert all(isinstance(x, String) for x in reconstructed)


def test_vector_json_serialization_integers():
    # Test vector of integers
    ints = [U32(1), U32(2), U32(3)]
    v = IntVector(ints)

    json_data = v.to_json()
    assert isinstance(json_data, list)
    assert json_data == [1, 2, 3]

    # Test deserialization
    reconstructed = IntVector.from_json(json_data)
    assert reconstructed == v
    assert all(isinstance(x, U32) for x in reconstructed)


def test_vector_json_serialization_booleans():
    # Test vector of booleans
    bools = [Boolean(True), Boolean(False), Boolean(True)]
    v = BoolVector(bools)

    json_data = v.to_json()
    assert isinstance(json_data, list)
    assert json_data == [True, False, True]

    # Test deserialization
    reconstructed = BoolVector.from_json(json_data)
    assert reconstructed == v
    assert all(isinstance(x, Boolean) for x in reconstructed)


def test_vector_json_empty():
    # Test empty vectors
    empty_str = StringVector()
    json_str = empty_str.to_json()
    assert json_str == []
    assert StringVector.from_json(json_str) == empty_str

    empty_int = IntVector()
    json_int = empty_int.to_json()
    assert json_int == []
    assert IntVector.from_json(json_int) == empty_int

    empty_bool = BoolVector()
    json_bool = empty_bool.to_json()
    assert json_bool == []
    assert BoolVector.from_json(json_bool) == empty_bool


def test_vector_json_invalid_input():
    # Test with invalid input types
    with pytest.raises(JsonDeserializationError):
        StringVector.from_json(None)  # None instead of list

    with pytest.raises(JsonDeserializationError):
        StringVector.from_json("not a list")  # String instead of list

    with pytest.raises(JsonDeserializationError):
        StringVector.from_json({})  # Dict instead of list

    # Test with invalid element types
    with pytest.raises(JsonDeserializationError):
        StringVector.from_json([1, 2, 3])  # Integers instead of strings

    with pytest.raises(JsonDeserializationError):
        IntVector.from_json(["1", "2", "3"])  # Strings instead of integers

    with pytest.raises(JsonDeserializationError):
        BoolVector.from_json([1, 0])  # Integers instead of booleans


def test_vector_json_roundtrip():
    # Test roundtrip for different types
    test_cases = [
        (StringVector([String("a"), String("b"), String("c")]), ["a", "b", "c"]),
        (IntVector([U32(1), U32(2), U32(3)]), [1, 2, 3]),
        (BoolVector([Boolean(True), Boolean(False)]), [True, False]),
    ]

    for original, expected_json in test_cases:
        json_data = original.to_json()
        assert json_data == expected_json

        reconstructed = original.__class__.from_json(
            json_data,
        )
        assert reconstructed == original
        assert isinstance(reconstructed, original.__class__)
        assert len(reconstructed) == len(original)


def test_vector_json_operations():
    # Test that JSON serialized and deserialized vectors maintain sequence operations
    original = StringVector([String("a"), String("b"), String("c")])
    json_data = original.to_json()
    reconstructed = StringVector.from_json(json_data)

    # Test indexing
    assert reconstructed[0] == String("a")
    assert reconstructed[-1] == String("c")

    # Test slicing
    assert reconstructed[1:] == StringVector([String("b"), String("c")])

    # Test iteration
    assert list(reconstructed) == list(original)

    # Test length
    assert len(reconstructed) == 3

    # Test contains
    assert String("b") in reconstructed
    assert String("x") not in reconstructed


def test_vector_json_special_values():
    # Test vector with special string values
    special_strings = StringVector(
        [
            String("Hello\nWorld"),  # Newline
            String("Tab\there"),  # Tab
            String("Unicode 世界"),  # Unicode
            String("Emoji 👋"),  # Emoji
        ]
    )

    json_data = special_strings.to_json()
    assert json_data == ["Hello\nWorld", "Tab\there", "Unicode 世界", "Emoji 👋"]

    reconstructed = StringVector.from_json(json_data)
    assert reconstructed == special_strings
    assert all(isinstance(x, String) for x in reconstructed)
