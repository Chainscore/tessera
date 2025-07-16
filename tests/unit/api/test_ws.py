from pathlib import Path
import statistics
import pytest
import asyncio
import json

from tsrkit_types import U32, Bytes
from jam.consensus.bp_engine import BlockProducer
from jam.execution.pvm.code import Code
from jam.network.node import Node
from jam.operations.utils.state_update import update_state
from jam.settings import setup_setting
from jam.state import accounts
from jam.state.accounts import Account
from jam.state.state import State, set_state, setup_state
from jam.state.utils import construct_state_key
from jam.statistics.statistics import Statistics
from jam.types.block import Block
from jam.consensus.grandpa.finality import Finality
from jam.api.rpc.app import rpc
from jam.api.rpc.broker import broker
from jam.types.protocol.core import ServiceId, TimeSlot
from jam.types.protocol.crypto import HeaderHash, Hash
from jam.types.state import delta
from jam.types.state.delta import AccountData, AccountMetadata, Delta, LookupTable, Timestamps
from jam.utils.dummy.dummy_block import create_dummy_block
from jam.utils.dummy.utils import create_dummy_bytes

from jam.types.protocol.core import Gas, Balance, BlobLength, ServiceId
from jam.types.protocol.crypto import Hash

from jam.types.state.delta import Ai, Ao, Timestamps, LookupTable

# Refred this : https://quart.palletsprojects.com/en/latest/how_to_guides/websockets/

def get_gen_state(db_path):
    # Load genesis state from jam/dev-spec.json
    setting = setup_setting(db_path, None)
    genesis_state_json = json.load(open(Path(__file__).parents[3] / "dev-spec.json"))["genesis_state"]
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
        blk.header.slot   = TimeSlot(i)
        hh = HeaderHash(blk.header.hash())
        state.transition(blk)
        parent = hh
        last_hh = hh
    return last_hh

@pytest.mark.asyncio
async def test_ws_finalized_block(db_path):
    # ——— set up on‐chain state just like the Node ———
    settings = setup_setting(db_path, 0, "alice", 0)
    state    = setup_state(settings.state_db)

    block = Block.genesis()
    hh    = block.save(settings.main_db)
    Finality.finalise(hh, settings.main_db)
    Finality.set_head(hh, settings.main_db)

    finalized_block = Finality.load_final(settings.main_db)
    expected = [
        list(finalized_block.header.hash()),
        int(finalized_block.header.slot)
    ]

    async with rpc.test_client() as client:
        async with client.websocket("/ws") as ws:

            await ws.send("finalizedBlock")
            # won't work without this sleep
            await asyncio.sleep(0.01)

            #make call to the finality function to test ws implementation
            Finality.finalise(hh, settings.main_db)
            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)
            assert data == expected

@pytest.mark.asyncio
async def test_ws_best_block(db_path):
    # ——— mirror the HTTP setup for bestBlock ———
    settings = setup_setting(db_path, 0, "alice", 0)
    state    = setup_state(settings.state_db)

    block = Block.genesis()
    hh    = block.save(settings.main_db)
    Finality.finalise(hh, settings.main_db)    
    Finality.set_head(hh, settings.main_db)

    expected = [ list(block.header.hash()), int(block.header.slot) ]

    #  open a WS & subscribe to the function
    async with rpc.test_client() as client:
        async with client.websocket("/ws") as ws:
            await ws.send("bestBlock")

            await asyncio.sleep(0.01)

            #make call to the finality set head function to test ws implementation
            Finality.set_head(hh, settings.main_db)
            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)

            assert data == expected


@pytest.mark.asyncio
async def test_ws_statistics(db_path):
    """
    Mirror the HTTP `test_statistics` but over WebSocket:
      – build a 5-block chain,
    """
 
    async with rpc.test_client() as client:
        async with client.websocket("/ws") as ws:
            # subscribe to statistics
            await ws.send("subscribeStatistics")

            await asyncio.sleep(0.01)
            state, settings = get_gen_state(db_path)
            db = settings.main_db
            produce_chain(state, db, 5)
            
            hh2 = db.get(Block.get_storage_key_slot(TimeSlot(2)))

            expected = [list((State.load(hh2).pi).encode())]

            raw = await asyncio.wait_for(ws.receive(), timeout=10)
            data = json.loads(raw)
            assert data == expected

@pytest.mark.asyncio
async def test_ws_service_data(db_path):
    

    async with rpc.test_client() as client:
        async with client.websocket("/ws") as ws:
            await ws.send("subscribeServiceData")
            await asyncio.sleep(0.01)
            
            # await broker.publish("subscribeServiceData", expected)
            state, settings = get_gen_state(db_path)
            db = settings.main_db
    
            update_state(state)
            state_delta_store = state.delta[ServiceId(42)].service.store
            expected = state_delta_store.get(bytes(construct_state_key((255, ServiceId(42)))))
            meta_expected = AccountMetadata.decode(expected)

            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)
            assert data == [list(meta_expected.encode())]

@pytest.mark.asyncio
async def test_ws_service_value(db_path):
    
    async with rpc.test_client() as client:
        async with client.websocket("/ws") as ws:
            await ws.send("subscribeServiceValue")
            await asyncio.sleep(0.01)
            
            state, settings = get_gen_state(db_path)
            set_state(state)
            db = settings.main_db

            data = create_dummy_bytes(100)
            sid = ServiceId(100)
            state.delta[sid] = AccountData()
            key = Bytes[32].fromhex("a3dc3bed1b0727caf428961bed11c9998ae2476d8a97fad203171b628363d9a2")
            value = Bytes[32]([0xB] * 32)
            state.delta[sid].storage[key] = value   
            produce_chain(state, db, 5)
            hh = db.get(Block.get_storage_key_slot(TimeSlot(2)))

            state_delta_store = state.delta[ServiceId(1)].service.store
            expected = [state.delta[sid].storage[key].hex()]

            expected = [list(value.hex())]

            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)
            assert data == expected

@pytest.mark.asyncio
async def test_ws_service_preimage(db_path):
    
    async with rpc.test_client() as client:
        async with client.websocket("/ws") as ws:
            await ws.send("subscribeServicePreimage")
            await asyncio.sleep(0.01)

            state, settings = get_gen_state(db_path)
            set_state(state)
            db = settings.main_db

            sid = ServiceId(2)
            state.delta[sid] = AccountData()
            blob = b"hello, there!"
            hsh  = blob  
            state.delta[sid].preimages[hsh] = blob

            produce_chain(state, db, 5)
            hh = db.get(Block.get_storage_key_slot(TimeSlot(2)))
            state_at_hh = State.load(hh)
            expected = list(state_at_hh.delta[sid].preimages[hsh])
            # await broker.publish("subscribeServicePreimage", expected)

            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)
            assert data == [expected]

@pytest.mark.asyncio
async def test_ws_service_request(db_path):

    state, settings = get_gen_state(db_path)
    set_state(state)
    db = settings.main_db

    sid = ServiceId(1)
    data = create_dummy_bytes(100)
    hash_val = Hash.blake2b(data)
    length   = 100

    state.delta[sid] = AccountData()
    state.delta[sid].lookup[LookupTable(hash=hash_val, length=length)] = Timestamps([U32(1752078176), U32(1752078177)])
    state.settle(header_hash=Bytes([1] * 32))

    produce_chain(state, db, 5)
    hh = db.get(Block.get_storage_key_slot(TimeSlot(2)))

    expected = [U32(1752078176), U32(1752078177)]

    async with rpc.test_client() as client:
        async with client.websocket("/ws") as ws:
            await ws.send("subscribeServiceRequest")
            await asyncio.sleep(0.01)
            await broker.publish("subscribeServiceRequest", expected)

            raw = await asyncio.wait_for(ws.receive(), timeout=5)
            data = json.loads(raw)

            assert data  == expected