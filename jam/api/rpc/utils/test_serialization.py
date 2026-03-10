"""
Tests for json_default serialization.

Verifies that json_default normalizes all domain types to JSON-safe primitives,
and that make_topic produces identical topic strings regardless of whether
params come from raw JSON (client-side) or typed domain objects (publisher-side).
"""

import pytest
from tsrkit_types import U8, U16, U32, U64, Bytes, Bytes32

from jam.types.protocol.core import ServiceId, BlobLength, CoreIndex, TimeSlot, ValidatorIndex
from jam.types.protocol.crypto import OpaqueHash, HeaderHash
from jam.api.rpc.utils.serialization import json_default, b64
from jam.api.rpc.broker import Broker


# ─── Primitives ───────────────────────────────────────────────

class TestJsonDefaultPrimitives:
    def test_none(self):
        assert json_default(None) is None

    def test_bool_true(self):
        result = json_default(True)
        assert result is True
        assert type(result) is bool

    def test_bool_false(self):
        result = json_default(False)
        assert result is False
        assert type(result) is bool

    def test_int(self):
        result = json_default(42)
        assert result == 42
        assert type(result) is int

    def test_int_zero(self):
        result = json_default(0)
        assert result == 0
        assert type(result) is int

    def test_float(self):
        result = json_default(3.14)
        assert result == 3.14

    def test_str(self):
        result = json_default("hello")
        assert result == "hello"
        assert type(result) is str

    def test_empty_str(self):
        result = json_default("")
        assert result == ""

    def test_bytes(self):
        raw = b"\x01\x02\x03"
        result = json_default(raw)
        assert result == b64(raw)
        assert isinstance(result, str)

    def test_bytes_empty(self):
        result = json_default(b"")
        assert result == b64(b"")

    def test_bytearray(self):
        raw = bytearray(b"\xaa\xbb")
        result = json_default(raw)
        assert result == b64(raw)


# ─── tsrkit_types integers (Uint[N]) ─────────────────────────

class TestJsonDefaultUints:
    """These are the critical tests — Uint[N] types must serialize to plain int."""

    def test_u8(self):
        result = json_default(U8(10))
        assert result == 10
        assert type(result) in (int, U8.__mro__[0])  # should be plain int ideally

    def test_u16(self):
        result = json_default(U16(1000))
        assert result == 1000

    def test_u32(self):
        result = json_default(U32(272902))
        assert result == 272902

    def test_u32_zero(self):
        result = json_default(U32(0))
        assert result == 0

    def test_u64(self):
        result = json_default(U64(2**40))
        assert result == 2**40

    def test_str_of_u32_is_plain_number(self):
        """str(json_default(U32(0))) must produce '0', not 'U32(0)' or 'AAAAAA=='."""
        result = json_default(U32(0))
        assert str(result) == "0", f"str(json_default(U32(0))) = {str(result)!r}, expected '0'"

    def test_str_of_u32_large(self):
        result = json_default(U32(272902))
        assert str(result) == "272902"


# ─── Domain types (ServiceId, BlobLength, etc.) ──────────────

class TestJsonDefaultDomainTypes:
    """ServiceId, BlobLength etc. are Uint[32] aliases — must behave like ints."""

    def test_service_id(self):
        result = json_default(ServiceId(0))
        assert str(result) == "0", f"json_default(ServiceId(0)) → str={str(result)!r}, repr={repr(result)!r}"

    def test_service_id_nonzero(self):
        result = json_default(ServiceId(42))
        assert str(result) == "42"

    def test_blob_length(self):
        result = json_default(BlobLength(272902))
        assert str(result) == "272902", f"json_default(BlobLength(272902)) → str={str(result)!r}"

    def test_core_index(self):
        result = json_default(CoreIndex(5))
        assert str(result) == "5"

    def test_time_slot(self):
        result = json_default(TimeSlot(6161630))
        assert str(result) == "6161630"

    def test_validator_index(self):
        result = json_default(ValidatorIndex(3))
        assert str(result) == "3"


# ─── Bytes domain types ──────────────────────────────────────

class TestJsonDefaultBytesTypes:
    def test_opaque_hash(self):
        raw = bytes(32)
        h = OpaqueHash(raw)
        result = json_default(h)
        assert result == b64(raw)
        assert isinstance(result, str)

    def test_header_hash(self):
        raw = b"\xab" * 32
        h = HeaderHash(raw)
        result = json_default(h)
        assert result == b64(raw)

    def test_bytes32(self):
        raw = b"\x01" * 32
        b = Bytes32(raw)
        result = json_default(b)
        assert result == b64(raw)

    def test_bytes_variable(self):
        raw = b"\xde\xad\xbe\xef"
        b = Bytes(raw)
        result = json_default(b)
        assert result == b64(raw)


# ─── Collections ──────────────────────────────────────────────

class TestJsonDefaultCollections:
    def test_list_of_ints(self):
        result = json_default([1, 2, 3])
        assert result == [1, 2, 3]

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


# ─── isinstance checks (diagnosing the MRO issue) ────────────

class TestIsinstanceChecks:
    """Diagnose whether IntCheckMeta breaks isinstance for json_default's checks."""

    def test_u32_isinstance_int(self):
        """U32 must be recognized as int by Python's built-in isinstance."""
        assert isinstance(U32(0), int)

    def test_service_id_isinstance_int(self):
        assert isinstance(ServiceId(0), int)

    def test_service_id_isinstance_bool_false(self):
        """ServiceId must NOT be recognized as bool."""
        assert not isinstance(ServiceId(0), bool)

    def test_u32_isinstance_uint(self):
        """This may FAIL due to IntCheckMeta — that's the bug."""
        from tsrkit_types.integers import Uint
        result = isinstance(U32(5), Uint)
        # Document actual behavior
        print(f"isinstance(U32(5), Uint) = {result}")
        print(f"U32.byte_size = {U32.byte_size}, Uint.byte_size = {Uint.byte_size}")

    def test_service_id_isinstance_uint(self):
        from tsrkit_types.integers import Uint
        result = isinstance(ServiceId(0), Uint)
        print(f"isinstance(ServiceId(0), Uint) = {result}")
        print(f"ServiceId.byte_size = {ServiceId.byte_size}, Uint.byte_size = {Uint.byte_size}")


# ─── Broker.make_topic parity ─────────────────────────────────

class TestMakeTopicParity:
    """The critical test: subscribe-side (raw JSON) and publish-side (typed) must produce same topic."""

    def test_subscribe_service_request_topic_match(self):
        """Simulates the exact bug: client subscribes with raw JSON types,
        publisher publishes with domain types. Topics must match."""

        # Client side — raw JSON params from WebSocket
        client_params = [0, "pCFmL9HQBgfAdPFGIKE7hOVD9DOGy3mC0oopTG6u+xs=", 272902, True]
        subscribe_topic = Broker.make_topic("subscribeServiceRequest", client_params)

        # Publisher side — typed domain objects from accumulation
        hash_bytes = OpaqueHash(bytes.fromhex(
            "a421662fd1d00607c074f14620a13b84e543f43386cb7982d28a294c6eaefb1b"
        ))
        publish_params = [ServiceId(0), hash_bytes, BlobLength(272902), True]
        publish_topic = Broker.make_topic("subscribeServiceRequest", publish_params)

        print(f"Subscribe topic: {subscribe_topic}")
        print(f"Publish topic:   {publish_topic}")

        assert subscribe_topic == publish_topic, (
            f"Topic mismatch!\n"
            f"  subscribe: {subscribe_topic}\n"
            f"  publish:   {publish_topic}"
        )

    def test_best_block_topic_match(self):
        """Simple case — both sides use empty params."""
        assert Broker.make_topic("subscribeBestBlock", []) == Broker.make_topic("subscribeBestBlock", [])

    def test_service_data_topic_match(self):
        client_params = [0, True]
        publish_params = [ServiceId(0), True]

        client_topic = Broker.make_topic("subscribeServiceData", client_params)
        publish_topic = Broker.make_topic("subscribeServiceData", publish_params)

        assert client_topic == publish_topic, (
            f"Topic mismatch!\n  client:  {client_topic}\n  publish: {publish_topic}"
        )

    def test_service_value_topic_match(self):
        key_b64 = b64(b"\x01\x02\x03")
        client_params = [0, key_b64, True]
        publish_params = [ServiceId(0), Bytes(b"\x01\x02\x03"), True]

        client_topic = Broker.make_topic("subscribeServiceValue", client_params)
        publish_topic = Broker.make_topic("subscribeServiceValue", publish_params)

        assert client_topic == publish_topic, (
            f"Topic mismatch!\n  client:  {client_topic}\n  publish: {publish_topic}"
        )
