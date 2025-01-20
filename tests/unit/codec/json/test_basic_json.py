from collections.abc import Sequence
from dataclasses import dataclass
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass
from jam.utils.codec.json.json_serializable import JsonSerializable

def test_basic_dc_json():
    @dataclass
    class TestModel(JsonSerializable):
        a: int
        b: str
        c: float
        d: bool

    data = {"a": 1, "b": "hello", "c": 3.14, "d": True}
    model = TestModel.from_json(data)
    assert model.a == 1
    assert model.b == "hello"
    assert model.c == 3.14
    assert model.d is True

def test_composite_json():
    @dataclass
    class TestModel(JsonSerializable):
        a: list[int]
        b: list[str]
        c: list[float]
        d: list[bool]

    data = {"a": [1, 2, 3], "b": ["hello", "world", "foo"], "c": [3.14, 2.71, 1.61], "d": [True, False, True]}
    model = TestModel.from_json(data)
    assert model.a == [1, 2, 3]
    assert model.b == ["hello", "world", "foo"]
    assert model.c == [3.14, 2.71, 1.61]
    assert model.d == [True, False, True]

def test_class_array_json():
    @decodable_dataclass
    @dataclass
    class CustomClass(Codable):
        a: int
        b: str
        c: float
        d: bool

    @decodable_dataclass
    @dataclass
    class TestModel(Codable):
        a: CustomClass

    data = {"a": {"a": 1, "b": "hello", "c": 3.14, "d": True}}
    model = TestModel.from_json(data)
    # Compare all values
    assert model.a.a == 1
    assert model.a.b == "hello"
    assert model.a.c == 3.14
    assert model.a.d is True