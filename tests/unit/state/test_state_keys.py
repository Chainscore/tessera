"""
construct_state_key encoding tests.

Pure unit tests — no fixtures, no state, no chain.
Verifies the interleaved key layout used by the state trie.
"""
import pytest

from jam.state.utils import construct_state_key
from jam.types.protocol.core import ServiceId
from jam.types.protocol.crypto import Hash
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U8


def test_single_u8_index():
    """U8 index -> [i, 0, 0, ...]"""
    for index in [U8(0), U8(1), U8(127), U8(255)]:
        result = construct_state_key(index)
        assert isinstance(result, Bytes)
        assert len(result) == 31
        assert int(result[0]) == index
        assert all(int(b) == 0 for b in result[1:])


def test_u8_service_id_pair():
    """(U8, ServiceId) -> [i, n0, 0, n1, 0, n2, 0, n3, 0, 0, ...]"""
    test_cases = [
        (U8(0), ServiceId(1)),
        (U8(1), ServiceId(1)),
        (U8(0xFF), ServiceId(1)),
        (U8(0), ServiceId(255)),
    ]

    for index, service_id in test_cases:
        result = construct_state_key((index, service_id))
        assert isinstance(result, Bytes)
        assert len(result) == 31
        assert result[0] == index.encode()[0]

        sid_enc = service_id.encode()
        for i, byte in enumerate(sid_enc):
            pos = 1 + i * 2
            if pos < 31:
                assert result[pos] == byte
                if pos + 1 < 31:
                    assert result[pos + 1] == 0


def test_service_id_hash_pair():
    """(ServiceId, Bytes32) -> [n0, h0, n1, h1, n2, h2, n3, h3, h4, ...]"""
    sid = ServiceId(1)
    key = Bytes([i % 256 for i in range(32)])
    result = construct_state_key((sid, key))
    assert isinstance(result, Bytes)
    assert len(result) == 31

    sid_enc = sid.encode()
    h = Hash.blake2b(key)
    for i in range(min(len(sid_enc), 4)):
        assert result[i * 2] == sid_enc[i]
        assert result[i * 2 + 1] == h[i]

    assert result[8:] == h[4:-5]


def test_invalid_inputs():
    with pytest.raises(ValueError):
        construct_state_key("invalid")
    with pytest.raises(ValueError):
        construct_state_key((U8(1), U8(2), U8(100)))
    with pytest.raises(ValueError):
        construct_state_key((ServiceId(1), "not_bytes"))


def test_boundary_conditions():
    assert len(construct_state_key(U8(0))) == 31
    assert len(construct_state_key(U8(255))) == 31
    assert len(construct_state_key((U8(0), ServiceId(0)))) == 31
    assert len(construct_state_key((U8(0xFF), ServiceId(255)))) == 31
    assert len(construct_state_key((ServiceId(0), Bytes([0] * 32)))) == 31
    assert len(construct_state_key((ServiceId(255), Bytes([255] * 32)))) == 31
