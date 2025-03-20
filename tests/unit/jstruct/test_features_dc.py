from dataclasses import dataclass
from typing import List
from jam.utils.jstruct import with_json_metadata
from jam.utils.jstruct.serde import JsonSerde


# Simple dataclass for basic testing
@with_json_metadata(
    name={"name": "fullName", "default": "John Doe"},
    age={"skip_if_none": True},
    active={"default": True},
    addresses={"default": []}
)
@dataclass
class Person(JsonSerde):
    name: str
    age: int
    active: bool
    addresses: List[str]

def test_dataclass_multiple_fields():
    # Test field with skip_if_none=True
    person = Person.from_json({"active": True})
    assert person.name == "John Doe"
    assert person.age == None
    assert person.active == True
    assert person.addresses == []