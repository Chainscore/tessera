"""
Tests for json_default serialization and Broker.make_topic parity.
"""
import pytest
from tsrkit_types import U32, U64, Bytes, Bytes32

from jam.types.protocol.core import ServiceId, BlobLength
from jam.types.protocol.crypto import OpaqueHash, HeaderHash
from jam.api.rpc.utils.serialization import json_default, b64
from jam.api.rpc.broker import Broker


class TestJsonDefaultPrimitives:
    def test_none(self):
        assert json_default(None) is None

    def test_bool(self):
        assert json_default(True) is True
        assert type(json_default(False)) is bool

    def test_int(self):
        assert json_default(42) == 42
        assert type(json_default(42)) is int

    def test_int_zero(self):
        assert json_default(0) == 0
        assert type(json_default(0)) is int

    def test_float(self):
        assert json_default(3.14) == 3.14

    def test_str(self):
        assert json_default("hello") == "hello"

    def test_bytes(self):
        raw = b"\x01\x02\x03"
        result = json_default(raw)
        assert result == b64(raw)
        assert isinstance(result, str)


class TestJsonDefaultUints:
    def test_u32(self):
        assert json_default(U32(272902)) == 272902

    def test_u64(self):
        assert json_default(U64(2**40)) == 2**40

    def test_str_of_u32_is_plain_number(self):
        """str(json_default(U32(0))) must produce '0', not 'U32(0)' or 'AAAAAA=='."""
        assert str(json_default(U32(0))) == "0"

    def test_str_of_u32_large(self):
        assert str(json_default(U32(272902))) == "272902"


class TestJsonDefaultDomainTypes:
    def test_service_id(self):
        assert str(json_default(ServiceId(0))) == "0"

    def test_blob_length(self):
        assert str(json_default(BlobLength(272902))) == "272902"


class TestJsonDefaultBytesTypes:
    def test_header_hash(self):
        raw = b"\xab" * 32
        assert json_default(HeaderHash(raw)) == b64(raw)

    def test_bytes_variable(self):
        raw = b"\xde\xad\xbe\xef"
        assert json_default(Bytes(raw)) == b64(raw)


class TestJsonDefaultCollections:
    def test_list_of_u32(self):
        result = json_default([U32(1), U32(2)])
        assert all(str(x) == str(i + 1) for i, x in enumerate(result))

    def test_dict(self):
        result = json_default({"key": U32(10), "data": b"\x01"})
        assert str(result["key"]) == "10"
        assert result["data"] == b64(b"\x01")

    def test_nested(self):
        result = json_default({"items": [U32(1), b"\xff"]})
        assert str(result["items"][0]) == "1"
        assert result["items"][1] == b64(b"\xff")


class TestMakeTopicParity:
    """Subscribe-side (raw JSON) and publish-side (typed) must produce same topic."""

    def test_service_request_topic_match(self):
        client_params = [0, "pCFmL9HQBgfAdPFGIKE7hOVD9DOGy3mC0oopTG6u+xs=", 272902, True]
        subscribe_topic = Broker.make_topic("subscribeServiceRequest", client_params)

        hash_bytes = OpaqueHash(bytes.fromhex(
            "a421662fd1d00607c074f14620a13b84e543f43386cb7982d28a294c6eaefb1b"
        ))
        publish_params = [ServiceId(0), hash_bytes, BlobLength(272902), True]
        publish_topic = Broker.make_topic("subscribeServiceRequest", publish_params)

        assert subscribe_topic == publish_topic

    def test_service_data_topic_match(self):
        client_topic = Broker.make_topic("subscribeServiceData", [0, True])
        publish_topic = Broker.make_topic("subscribeServiceData", [ServiceId(0), True])
        assert client_topic == publish_topic

    def test_service_value_topic_match(self):
        key_b64 = b64(b"\x01\x02\x03")
        client_topic = Broker.make_topic("subscribeServiceValue", [0, key_b64, True])
        publish_topic = Broker.make_topic("subscribeServiceValue", [ServiceId(0), Bytes(b"\x01\x02\x03"), True])
        assert client_topic == publish_topic
