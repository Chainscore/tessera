# jam/tests/unit/api/test_rpc.py
import pytest
import os
from jam.finality.finality import Finality

from jam.settings import setup_setting
from jam.api.rpc.app import rpc
from jam.state.state import setup_state, State
from jam.state.utils import construct_state_key
from jam.block.block import Block
from jam.state.accounts import AccountData
from jam.types.protocol.core import ServiceId, TimeSlot
from jam.types.protocol.crypto import Hash
from jam.types.state.delta import LookupTable, Timestamps
from tsrkit_types import U32, ByteArray, Bytes, TypedArray
from jam.utils.dummy.utils import create_dummy_bytes
from tests.unit.api.utils import produce_chain, init_chain


target_code = bytes([0, 0, 22, 124, 121, 81, 25, 1, 7, 40, 2, 0, 149, 17, 255, 70, 1, 1, 100, 23, 51, 8, 1, 50, 0, 69, 147, 18])
target_code_hash = Hash.blake2b(target_code)
target_service = ServiceId(69)

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_best_block(db_path):
    settings = setup_setting(db_path, 0, "alice", 0)
    state = setup_state(settings.state_db)

    block = Block.genesis()
    hh = block.save(settings.main_db)  # Save to test-specific DB
    Finality.set_head(block, settings.main_db)
    Finality.finalise(block, settings.main_db, True)
    b1 = block.produce(TimeSlot(1), state, None)
    state.transition(b1)

    # Simulate the best block handler
    payload = {"method": "bestBlock", "jsonrpc": "2.0", "params": [], "id": 3}

    response = await rpc.test_client().post("/", json=payload)
    assert response.status_code == 200
    data = await response.get_json()

    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert data["result"]["header_hash"] == list(b1.header.hash())
    assert data["result"]["slot"] == int(b1.header.slot)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_finalized_block(db_path):
    settings = setup_setting(db_path, 0, "alice", 0)
    state = setup_state(settings.state_db)

    block = Block.genesis()
    hh = block.save(settings.main_db)  # Save to test-specific DB
    Finality.set_head(block, settings.main_db)
    Finality.finalise(block, settings.main_db)

    finalized_block = Finality.load_final(settings.main_db)

    # Simulate the finalized block handler
    payload = {"method": "finalizedBlock", "jsonrpc": "2.0", "params": [], "id": 3}

    response = await rpc.test_client().post("/", json=payload)
    assert response.status_code == 200
    data = await response.get_json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert data["result"]["header_hash"] == list(finalized_block.header.hash())
    assert data["result"]["slot"] == int(finalized_block.header.slot)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_parent_block(db_path):
    # Setup Node and Build a chain of 5 blocks
    _, settings = produce_chain(db_path)

    # hash of slot‐3’s block
    hh3 = settings.main_db.get(Block.get_storage_key_slot(TimeSlot(3)))

    # hash of slot‐2’s block
    hh2 = settings.main_db.get(Block.get_storage_key_slot(TimeSlot(2)))

    # Simulate the parent block handler
    payload = {"method": "parent", "jsonrpc": "2.0", "params": [list(hh3)], "id": 3}
    response = await rpc.test_client().post("/", json=payload)
    assert response.status_code == 200
    data = await response.get_json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert data["result"]["header_hash"] == list(hh2)
    assert data["result"]["slot"] == int(2)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_state_root(db_path):
    # Setup Node and Build a chain of 5 blocks
    _, settings = produce_chain(db_path)

    # hash of slot‐3’s block
    hh3 = settings.main_db.get(Block.get_storage_key_slot(TimeSlot(3)))

    # Call the RPC
    payload = {"method": "stateRoot", "jsonrpc": "2.0", "params": [list(hh3)], "id": 3}
    resp = await rpc.test_client().post("/", json=payload)
    assert resp.status_code == 200
    data = await resp.get_json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert data["result"]["header_hash"] == list(bytes(State.load(hh3).root).hex())


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_statistics(db_path):
    # Setup Node and Build a chain of 5 blocks
    _, settings = produce_chain(db_path)

    # hash of slot‐2’s block
    hh2 = settings.main_db.get(Block.get_storage_key_slot(TimeSlot(2)))

    # Call the RPC
    payload = {"method": "statistics", "jsonrpc": "2.0", "params": [list(hh2)], "id": 3}

    resp = await rpc.test_client().post("/", json=payload)
    assert resp.status_code == 200
    data = await resp.get_json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert data["result"]["result"] == list(((State.load(hh2).pi).encode()).hex())


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_service_data_rpc(db_path):
    state, settings, b0 = init_chain(db_path)

    # Make updates
    sid = ServiceId(2)
    state.delta[sid] = AccountData()

    # Tweak Delta & Settle state first
    assert state.delta[sid].service.code_hash == Bytes(32)
    state.settle(header_hash=Bytes([1] * 32))

    state, settings = produce_chain(db_path, False)

    # hash of slot‐2’s block
    hh2 = settings.main_db.get(Block.get_storage_key_slot(TimeSlot(2)))
    service_store = state.delta[sid].service.store
    expected_data = service_store.get(bytes(construct_state_key((255, sid))))

    # call the RPC
    payload = {"method": "serviceData", "jsonrpc": "2.0", "params": [list(hh2), int(sid)], "id": 7}
    resp = await rpc.test_client().post("/", json=payload)
    assert resp.status_code == 200
    data = await resp.get_json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 7
    assert data["result"]["result"] == list(expected_data)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_service_value_rpc(db_path):
    state, settings, b0 = init_chain(db_path)

    # pick a service and store a value under some key
    state.delta[ServiceId(1)] = AccountData()
    sid = ServiceId(1)
    key = Bytes[32]([0xA] * 32)
    value = Bytes[32]([0xB] * 32)

    # Tweak Delta & Settle state first
    state.delta[sid].storage[key] = value
    state.settle(header_hash=Bytes([1] * 32))

    state, settings = produce_chain(db_path, False)
    hh = settings.main_db.get(Block.get_storage_key_slot(TimeSlot(2)))

    payload = {
        "method": "serviceValue",
        "jsonrpc": "2.0",
        "params": [list(hh), int(1), list(key)],
        "id": 8,
    }

    resp = await rpc.test_client().post("/", json=payload)
    data = await resp.get_json()
    assert resp.status_code == 200
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 8
    assert data["result"]["result"] == list(str(value.hex()))


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_service_preimage_rpc(db_path):
    state, settings, b0 = init_chain(db_path)

    sid = ServiceId(9)
    state.delta[sid] = AccountData()
    blob = b"hello, there!"
    hsh = Hash.blake2b(blob)

    # Tweak Delta & Settle state first
    state.delta[sid].preimages[hsh] = blob
    state.settle(header_hash=Bytes([1] * 32))

    state, settings = produce_chain(db_path, False)

    # hash of slot‐3’s block
    hh = settings.main_db.get(Block.get_storage_key_slot(TimeSlot(3)))

    payload = {
        "method": "servicePreimage",
        "jsonrpc": "2.0",
        "params": [list(hh), int(sid), list(hsh)],
        "id": 9,
    }
    resp = await rpc.test_client().post("/", json=payload)
    data = await resp.get_json()
    assert resp.status_code == 200
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 9
    assert data["result"]["result"] == list(blob.hex())


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_service_request_handler_rpc(db_path):
    state, settings, b0 = init_chain(db_path)

    sid = ServiceId(1)
    data = create_dummy_bytes(100)

    hash = Hash.blake2b(data)

    len = 100
    state.delta[sid] = AccountData()
    state.delta[sid].lookup[LookupTable(hash=hash, length=len)] = Timestamps(
        [U32(1752078176), U32(1752078177)]
    )

    state.settle(header_hash=Bytes([1] * 32))

    state, settings = produce_chain(db_path, False)

    # hash of slot‐2’s block
    hh = settings.main_db.get(Block.get_storage_key_slot(TimeSlot(2)))

    payload = {
        "method": "serviceRequest",
        "jsonrpc": "2.0",
        "params": [list(hh), int(sid), list(hash), int(len)],
        "id": 9,
    }
    resp = await rpc.test_client().post("/", json=payload)
    data = await resp.get_json()
    assert resp.status_code == 200
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 9
    assert data["result"]["result"] == [U32(1752078176), U32(1752078177)]
