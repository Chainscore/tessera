from dataclasses import dataclass
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
    @dataclass
    class CustomClass():
        a: int
        b: str
        c: float
        d: bool

    @dataclass
    class TestModel(JsonSerializable):
        a: list[CustomClass]
        d: list[bool]

    data = {"a": [{"a": 1, "b": "hello", "c": 3.14, "d": True}, {"a": 2, "b": "world", "c": 2.71, "d": False}], "d": [True, False, True]}
    model = TestModel.from_json(data)
    # Compare a
    assert model.a[0].a == 1
    assert model.a[0].b == "hello"
    assert model.a[0].c == 3.14
    assert model.a[0].d is True
    assert model.a[1].a == 2
    assert model.a[1].b == "world"
    assert model.a[1].c == 2.71
    assert model.a[1].d is False
    assert model.d == [True, False, True]