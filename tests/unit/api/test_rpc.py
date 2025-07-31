# jam/tests/unit/api/test_rpc.py
import pytest
import json
from pathlib import Path
from jam.settings import setup_setting
from jam.api.rpc.app import rpc
from jam.state.state import setup_state, set_state, State
from jam.state.utils import construct_state_key
from jam.types.block import Block
from jam.consensus.grandpa.finality import Finality
from jam.consensus.bp_engine import BlockProducer
from jam.network.node import Node
from jam.state.accounts import DeltaView, AccountData, StorageView, PreImageView, TimestampsView
from jam.types.state.delta import LookupTable, ServiceCodeHash, Ao, Ai, Timestamps
from jam.types.protocol.core import Balance, Gas, ServiceId, TimeSlot
from jam.utils.dummy.dummy_block import create_dummy_block
from jam.types.protocol.crypto import HeaderHash, OpaqueHash, Hash
from jam.types.state.delta import LookupTable, Timestamps
from tsrkit_types import U32, ByteArray, Bytes, TypedArray
from jam.utils.dummy.utils import create_dummy_bytes


def get_gen_state(db_path):
    # Load genesis state
    setting = setup_setting(db_path, None)
    genesis_state_json = json.load(open(Path(__file__).parents[3] / "dev-spec.json"))[
        "genesis_state"
    ]
    state = State.from_keyvals(genesis_state_json, setting.state_db)
    state.store.enable_cache()
    state.store.enable_writes()
    return state, setting


def produce_chain(state, db, length, starting_parent=None):
    """
    Execute `length` dummy blocks onto `db`, each with consecutive
    TimeSlot(0), TimeSlot(1), …
    Returns the HeaderHash of the last block.
    """
    parent = starting_parent or HeaderHash([0] * 32)
    last_hh = None
    for i in range(length):
        blk = Block.genesis()
        blk.header.parent = parent
        blk.header.slot = TimeSlot(i)
        hh = HeaderHash(blk.header.hash())
        state.transition(blk)
        parent = hh
        last_hh = hh
    return last_hh


@pytest.mark.asyncio
async def test_best_block(db_path):
    settings = setup_setting(db_path, 0, "alice", 0)
    state = setup_state(settings.state_db)

    block = Block.genesis()
    hh = block.save(settings.main_db)  # Save to test-specific DB
    Finality.finalise(hh, settings.main_db)
    Finality.set_head(hh, settings.main_db)
    b1 = BlockProducer(
        node=Node("", "", 0, settings.val, [], False, False), db=settings.main_db
    )._produce_block(state, TimeSlot(1))
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
async def test_finalized_block(db_path):
    settings = setup_setting(db_path, 0, "alice", 0)
    state = setup_state(settings.state_db)

    block = Block.genesis()
    hh = block.save(settings.main_db)  # Save to test-specific DB
    Finality.finalise(hh, settings.main_db)
    Finality.set_head(hh, settings.main_db)

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
async def test_parent_block(db_path):
    settings = setup_setting(db_path, 0, "alice", 0)
    state = setup_state(settings.state_db)

    block = Block.genesis()
    hh = block.save(settings.main_db)  # Save to test-specific DB
    Finality.finalise(hh, settings.main_db)
    Finality.set_head(hh, settings.main_db)

    b1 = BlockProducer(
        node=Node("", "", 0, settings.val, [], False, False), db=settings.main_db
    )._produce_block(state, TimeSlot(1))
    state.transition(b1)
    b2 = BlockProducer(
        node=Node("", "", 0, settings.val, [], False, False), db=settings.main_db
    )._produce_block(state, TimeSlot(2))
    state.transition(b2)

    # Simulate the parent block handler
    payload = {"method": "parent", "jsonrpc": "2.0", "params": [list(b2.header.hash())], "id": 3}
    response = await rpc.test_client().post("/", json=payload)
    assert response.status_code == 200
    data = await response.get_json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert data["result"]["header_hash"] == list(b1.header.hash())
    assert data["result"]["slot"] == int(b1.header.slot)


@pytest.mark.asyncio
async def test_state_root(db_path):
    # setup: get a State
    settings = setup_setting(db_path, None)
    state = setup_state(settings.state_db)
    db = settings.main_db
    block = Block.genesis()
    hh = block.save(settings.main_db)  # Save to test-specific DB
    Finality.finalise(hh, settings.main_db)
    Finality.set_head(hh, settings.main_db)

    # churn 5 blocks (slots 1–5)
    produce_chain(state, settings.main_db, length=5)

    # hash of slot‐4’s block
    hh4 = db.get(Block.get_storage_key_slot(TimeSlot(2)))

    # Call the RPC
    payload = {"method": "stateRoot", "jsonrpc": "2.0", "params": [list(hh4)], "id": 3}
    resp = await rpc.test_client().post("/", json=payload)
    assert resp.status_code == 200
    data = await resp.get_json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert data["result"]["header_hash"] == list(bytes(State.load(hh4).root).hex())


@pytest.mark.asyncio
async def test_statistics(db_path):
    settings = setup_setting(db_path, None)
    state = setup_state(settings.state_db)
    db = settings.main_db
    block = Block.genesis()
    hh = block.save(settings.main_db)  # Save to test-specific DB
    Finality.finalise(hh, settings.main_db)
    Finality.set_head(hh, settings.main_db)

    # churn 5 blocks (slots 1–5)
    produce_chain(state, settings.main_db, length=5)

    hh2 = db.get(Block.get_storage_key_slot(TimeSlot(2)))
    # Call the RPC
    payload = {"method": "statistics", "jsonrpc": "2.0", "params": [list(hh2)], "id": 3}

    resp = await rpc.test_client().post("/", json=payload)
    assert resp.status_code == 200
    data = await resp.get_json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert data["result"]["result"] == list(((State.load(hh2).pi).encode()).hex())


@pytest.mark.asyncio
async def test_service_data_rpc(db_path):
    state, settings = get_gen_state(db_path)
    db = settings.main_db

    # Make updates
    sid = ServiceId(2)
    state.delta[sid] = AccountData()

    assert state.delta[sid].service.code_hash == Bytes(32)

    # hash of slot‐2’s block
    parent = HeaderHash([0] * 32)
    for i in range(5):
        blk = create_dummy_block()
        blk.header.parent = parent
        blk.header.slot = TimeSlot(i)
        hh = HeaderHash(blk.header.hash())
        state.transition(blk)
        state.settle(hh)
        blk.save(db)
        Finality.set_head(hh, db)
        Finality.finalise(hh, db)
        parent = hh

    hh = db.get(Block.get_storage_key_slot(TimeSlot(2)))
    service_store = state.delta[sid].service.store
    expected_data = service_store.get(bytes(construct_state_key((255, sid))))

    # call the RPC
    payload = {"method": "serviceData", "jsonrpc": "2.0", "params": [list(hh), int(sid)], "id": 7}
    resp = await rpc.test_client().post("/", json=payload)
    assert resp.status_code == 200
    data = await resp.get_json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 7
    assert data["result"]["result"] == list(expected_data)


@pytest.mark.asyncio
async def test_service_value_rpc(db_path):
    settings = setup_setting(db_path, None)
    state = setup_state(settings.state_db)
    db = settings.main_db
    block = Block.genesis()
    hh = block.save(settings.main_db)  # Save to test-specific DB
    Finality.finalise(hh, settings.main_db)
    Finality.set_head(hh, settings.main_db)

    # pick a service and store a value under some key
    data = create_dummy_bytes(100)

    state.delta[ServiceId(1)] = AccountData()
    sid = ServiceId(1)
    key = Bytes[32]([0xA] * 32)
    value = Bytes[32]([0xB] * 32)
    state.delta[sid].storage[key] = value

    produce_chain(state, settings.main_db, length=5)
    hh = db.get(Block.get_storage_key_slot(TimeSlot(2)))

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
async def test_service_preimage_rpc(db_path):
    settings = setup_setting(db_path, None)
    state = setup_state(settings.state_db)
    db = settings.main_db
    block = Block.genesis()
    hh = block.save(settings.main_db)  # Save to test-specific DB
    Finality.finalise(hh, settings.main_db)
    Finality.set_head(hh, settings.main_db)

    sid = ServiceId(9)
    state.delta[sid] = AccountData()
    blob = b"hello, there!"
    # hash function as above
    hsh = blob  # replace with real blake2b(blob)
    state.delta[sid].preimages[hsh] = blob

    # hash of slot‐2’s block
    produce_chain(state, settings.main_db, 5)
    hh = db.get(Block.get_storage_key_slot(TimeSlot(2)))

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
async def test_service_request_handler_rpc(db_path):
    settings = setup_setting(db_path, None)
    state = setup_state(settings.state_db)
    db = settings.main_db
    block = Block.genesis()
    hh = block.save(settings.main_db)  # Save to test-specific DB
    Finality.finalise(hh, settings.main_db)
    Finality.set_head(hh, settings.main_db)

    set_state(state)
    db = settings.main_db

    sid = ServiceId(1)
    data = create_dummy_bytes(100)

    hash = Hash.blake2b(data)

    len = 100
    state.delta[sid] = AccountData()
    state.delta[sid].lookup[LookupTable(hash=hash, length=len)] = Timestamps(
        [U32(1752078176), U32(1752078177)]
    )

    state.settle(header_hash=Bytes([1] * 32))

    # hash of slot‐2’s block
    produce_chain(state, settings.main_db, 5)
    hh = db.get(Block.get_storage_key_slot(TimeSlot(2)))

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
