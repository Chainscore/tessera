import pytest
from dataclasses import dataclass
from typing import Dict, Optional
from jam.utils.jstruct import with_json_metadata
from jam.utils.jstruct.serde import JsonFieldError, JsonSerde
from jam.types.base.string import String
from jam.types.base.boolean import Boolean
from jam.types.base.integers.fixed import I32 as Int32
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.base.dictionary import Dictionary, decodable_dictionary


# Simple dataclass for basic testing
@with_json_metadata(
    name={"name": "fullName"},
    age={"skip_if_none": True},
    active={"default": True}
)
@dataclass
class Person(JsonSerde):
    name: str
    age: int
    active: bool


# Dataclass with custom field handling
@with_json_metadata(
    title={"name": "displayTitle", "skip_if_none": True}, 
    description={"name": "desc"}
)
@dataclass
class Document(JsonSerde):
    id: str
    title: Optional[str] = None
    description: str = "No description"


# Nested dataclass with JAM types
@decodable_vector(String)
class StringVector(Vector[String]):
    ...


@decodable_dictionary(String, Int32)
class StringIntDict(Dictionary[String, Int32]):
    ...


@with_json_metadata(
    metadata={"name": "metadata", "skip_if_none": True}
)
@dataclass
class ComplexData(JsonSerde):
    strings: StringVector
    numbers: StringIntDict
    flags: Dict
    metadata: Optional[Dict]


def test_simple_dataclass_serialization():
    # Test basic serialization
    person = Person(name="John Doe", age=30, active=True)
    json_data = person.to_json()

    assert isinstance(json_data, dict)
    assert json_data["fullName"] == "John Doe"
    assert json_data["age"] == 30
    assert json_data["active"] is True

    # Test deserialization
    reconstructed = Person.from_json(json_data)
    assert reconstructed == person
    assert reconstructed.name == "John Doe"
    assert reconstructed.age == 30
    assert reconstructed.active is True


def test_dataclass_field_options():
    # Test field with skip_if_none=True
    person = Person(name="John Doe", age=None, active=True)
    json_data = person.to_json()
    assert "age" not in json_data
    assert json_data["fullName"] == "John Doe"

    # Test custom field names
    assert "fullName" in json_data
    assert "name" not in json_data


def test_dataclass_with_metadata():
    # Test metadata handling
    doc = Document(id="123", title=None, description="Test document")

    json_data = doc.to_json()
    print("json_data", json_data)
    assert json_data["id"] == "123"
    assert "displayTitle" not in json_data  # Skipped because None
    assert json_data["desc"] == "Test document"

    # Test deserialization
    reconstructed = Document.from_json(json_data)
    assert reconstructed.id == "123"
    assert reconstructed.title is None
    assert reconstructed.description == "Test document"


def test_nested_dataclass():
    # Create complex data with nested types
    data = ComplexData(
        strings=StringVector([String("one"), String("two")]),
        numbers=StringIntDict({String("a"): Int32(1), String("b"): Int32(2)}),
        flags={"flag1": Boolean(True), "flag2": Boolean(False)},
        metadata={"key": "value"},
    )

    json_data = data.to_json()

    # Check structure
    assert isinstance(json_data, dict)
    assert isinstance(json_data["strings"], list)
    assert isinstance(json_data["numbers"], dict)
    assert isinstance(json_data["flags"], dict)
    assert isinstance(json_data["metadata"], dict)

    # Check values
    assert json_data["strings"] == ["one", "two"]
    assert json_data["numbers"] == {"a": 1, "b": 2}
    assert json_data["flags"] == {"flag1": True, "flag2": False}
    assert json_data["metadata"] == {"key": "value"}

    # Test deserialization
    print("json_data", json_data)
    reconstructed = ComplexData.from_json(json_data)
    assert reconstructed == data


def test_dataclass_invalid_input():
    # Test missing required field
    with pytest.raises(JsonFieldError):
        Person.from_json({"age": 30})  # Missing name

    # Test invalid field type
    with pytest.raises(JsonFieldError):
        Person.from_json({"fullName": "John", "age": "not a number"})  # Should be int

    # Test invalid nested type
    with pytest.raises(JsonFieldError):
        ComplexData.from_json(
            {
                "strings": [1, 2, 3],  # Should be strings
                "numbers": {"a": 1},
                "flags": {},
            }
        )


def test_dataclass_inheritance():
    @dataclass(kw_only=True)
    class BaseClass(JsonSerde):
        id: str

    @with_json_metadata(
        id={"name": "identifier"},
        name={"name": "fullName"}
    )
    @dataclass
    class DerivedClass(BaseClass):
        name: str

    # Test inheritance handling
    obj = DerivedClass(id="123", name="test")
    json_data = obj.to_json()

    print("json_data", json_data)

    assert json_data["identifier"] == "123"
    assert json_data["fullName"] == "test"

    reconstructed = DerivedClass.from_json(json_data)
    assert reconstructed == obj
    assert reconstructed.id == "123"
    assert reconstructed.name == "test"


def test_dataclass_optional_fields():
    @with_json_metadata(
        required={"name": "required"},
        optional_str={"skip_if_none": True},
        with_default={"default": 42}
    )
    @dataclass
    class OptionalFields(JsonSerde):
        required: str
        optional_str: Optional[str] = None
        with_default: int = 42

    # Test with all fields
    obj1 = OptionalFields("required", "optional_str", 100)
    json_data = obj1.to_json()
    assert json_data["required"] == "required"
    assert json_data["optional_str"] == "optional_str"
    assert json_data["with_default"] == 100

    # Test with optional field as None
    obj2 = OptionalFields("required")
    json_data = obj2.to_json()
    assert json_data["required"] == "required"
    assert json_data.get("optional_str") is None
    assert json_data["with_default"] == 42

    # Test deserialization with missing optional field
    reconstructed = OptionalFields.from_json({"required": "test"})
    assert reconstructed.required == "test"
    assert reconstructed.optional_str is None
    assert reconstructed.with_default == 42


def test_dataclass_field_metadata():
    @with_json_metadata(
        field1={"name": "jsonField1", "skip_if_none": True},
        field2={"name": "jsonField2", "skip_if_none": True, "default": None},
        field3={"name": "jsonField3"}
    )
    @dataclass
    class MetadataTest(JsonSerde):
        field1: str
        field2: Optional[str]
        field3: str

    # Test skip_if_none behavior
    obj = MetadataTest(field1=None, field2=None, field3="test")
    json_data = obj.to_json()

    assert "jsonField1" not in json_data
    assert "jsonField2" not in json_data
    assert json_data["jsonField3"] == "test"

    # Test deserialization with minimal fields
    reconstructed = MetadataTest.from_json({"jsonField3": "test"})
    assert reconstructed.field1 is None
    assert reconstructed.field2 is None
    assert reconstructed.field3 == "test"
