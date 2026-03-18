"""
State mutation tests — delta CRUD, stash, settle, root changes.

Tests direct state manipulation: write to delta, stash, settle,
verify root changes and data persists. Uses jam_node fixture (genesis only).
"""
from jam.types.protocol.core import ServiceId, Balance, TimeSlot
from jam.types.protocol.crypto import Hash
from jam.types.state.delta import LookupTable, Timestamps
from tsrkit_types import Bytes, U32, U64


class TestGenesisState:

    async def test_tau_is_zero(self, jam_node):
        assert jam_node.state.tau == 0

    async def test_root_is_nonzero(self, jam_node):
        root = jam_node.state.root
        assert root != bytes(32)
        assert len(root) == 32

    async def test_bootstrap_service_exists(self, jam_node):
        acct = jam_node.state.delta.get(ServiceId(0))
        assert acct is not None

    async def test_kappa_has_validators(self, jam_node):
        assert len(jam_node.state.kappa) > 0


class TestDeltaMetadata:
    """Service metadata write/read through delta."""

    async def test_read_existing_service(self, jam_node):
        original = jam_node.state.delta[ServiceId(0)].service
        assert original.code_hash is not None

    async def test_update_balance(self, jam_node):
        state = jam_node.state
        sid = ServiceId(0)
        state.delta[sid].service.balance = Balance(9999999)
        assert state.delta[sid].service.balance == Balance(9999999)

    async def test_full_metadata_roundtrip(self, jam_node):
        """Write all metadata fields, read them back."""
        state = jam_node.state
        sid = ServiceId(0)
        meta = state.delta[sid].service

        meta.balance = Balance(42)
        meta.gas_limit = U64(500000)
        meta.min_gas = U64(100)

        read = state.delta[sid].service
        assert read.balance == Balance(42)
        assert read.gas_limit == U64(500000)
        assert read.min_gas == U64(100)


class TestDeltaStorage:
    """Storage key-value write/read/delete through delta."""

    async def test_write_read(self, jam_node):
        state = jam_node.state
        key = Bytes(b"test_key_storage")
        val = Bytes(b"test_value_batman")

        state.delta[ServiceId(0)].storage[key] = val
        assert state.delta[ServiceId(0)].storage[key] == val

    async def test_delete(self, jam_node):
        state = jam_node.state
        sid = ServiceId(0)
        key = Bytes(b"ephemeral_key")
        val = Bytes(b"ephemeral_val")

        state.delta[sid].storage[key] = val
        assert state.delta[sid].storage[key] == val

        del state.delta[sid].storage[key]
        assert state.delta[sid].storage[key] is None

    async def test_overwrite(self, jam_node):
        state = jam_node.state
        sid = ServiceId(0)
        key = Bytes(b"overwrite_key")

        state.delta[sid].storage[key] = Bytes(b"first")
        state.delta[sid].storage[key] = Bytes(b"second")
        assert state.delta[sid].storage[key] == Bytes(b"second")


class TestDeltaPreimages:
    """Preimage store/read through delta."""

    async def test_write_read(self, jam_node):
        state = jam_node.state
        blob = b"hello from state preimage test"
        blob_hash = Hash.blake2b(blob)

        state.delta[ServiceId(0)].preimages[blob_hash] = Bytes(blob)
        assert state.delta[ServiceId(0)].preimages[blob_hash] == Bytes(blob)

    async def test_nonexistent_is_none(self, jam_node):
        fake = Hash.blake2b(b"nonexistent")
        assert jam_node.state.delta[ServiceId(0)].preimages[fake] is None


class TestDeltaTimestamps:
    """Lookup table timestamp write/read through delta."""

    async def test_write_read(self, jam_node):
        state = jam_node.state
        data = b"timestamps_test_data"
        key = LookupTable(hash=Hash.blake2b(data), length=len(data))
        ts = Timestamps([U32(100), U32(200)])

        state.delta[ServiceId(0)].lookup[key] = ts
        assert state.delta[ServiceId(0)].lookup[key] == ts

    async def test_empty_timestamps(self, jam_node):
        """Empty timestamps = solicitation."""
        state = jam_node.state
        data = b"solicited_data"
        key = LookupTable(hash=Hash.blake2b(data), length=len(data))

        state.delta[ServiceId(0)].lookup[key] = Timestamps([])
        assert state.delta[ServiceId(0)].lookup[key] == Timestamps([])


class TestStashSettle:
    """Stash records changes, settle commits them — root changes."""

    async def test_root_changes_after_stash_settle(self, jam_node):
        state = jam_node.state
        root_before = state.root.hex()

        state.tau = TimeSlot(1)

        hh = jam_node.grandpa.load_final().header.hash()
        state.stash(hh)
        state.settle(hh)

        assert state.root.hex() != root_before

    async def test_delta_persists_after_settle(self, jam_node):
        state = jam_node.state
        sid = ServiceId(0)
        state.delta[sid].service.balance = Balance(7777)

        hh = jam_node.grandpa.load_final().header.hash()
        state.stash(hh)
        state.settle(hh)

        assert state.delta[sid].service.balance == Balance(7777)
