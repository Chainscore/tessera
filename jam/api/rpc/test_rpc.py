import pytest
import pytest_asyncio
import tempfile
import shutil
from jam.api.rpc.main import app
from jam.db.kv import KVStore
from jam.state.ghost import GhostState
from jam.state.state import setup_state
from jam.types.block import Block
from jam.types.header import Header
from jam.consensus.grandpa.finality import Finality
from jam.config import data_stores
from jam.consensus.bp_engine import BlockProducer
from jam.network.node import Node
from jam.types.protocol.core import TimeSlot



@pytest_asyncio.fixture(scope="function")
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db = KVStore(temp_dir)
    setup_state(GhostState.genesis(), db)
    from jam.state.state import state as updated_state

    # Inject test DB into global for the handlers
    data_stores.main_db = db

    yield db
    shutil.rmtree(temp_dir)

@pytest_asyncio.fixture
async def test_client():
    async with app.test_app():
        yield app.test_client()

@pytest.mark.asyncio
async def test_best_block(test_client, temp_db):
    block = Block.genesis()
    block.save(temp_db)  # Save to test-specific DB
    
    # Simulate the best block handler
    payload = {
        "method": "bestBlock",
        "jsonrpc": "2.0",
        "params": {},
        "id": 3
    }

    response = await test_client.post("/rpc", json=payload)
    assert response.status_code == 200
    data = await response.get_json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert isinstance(data["result"], list)
    assert len(data["result"]) == 2
    assert data["result"][0] == Header.__hash__(block.header)
    assert data["result"][1] == int(block.header.slot)

@pytest.mark.asyncio
async def test_finalized_block(test_client, temp_db):
    # Simulate the finalized block
    # Create a block and finalize it
    block = Block.from_random()
    Finality.finalise(block.header.slot, temp_db)
    block.save(temp_db)
    
    # Load the finalized block to check the finality
    finalized_block = Finality.load_final(temp_db)
    # Simulate the finalized block handler
    payload = {
        "method": "finalizedBlock",
        "jsonrpc": "2.0",
        "params": {},
        "id": 3
    }

    response = await test_client.post("/rpc", json=payload)
    assert response.status_code == 200
    data = await response.get_json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert isinstance(data["result"], list)
    assert len(data["result"]) == 2
    assert data["result"][0] == Header.__hash__(finalized_block.header)
    assert data["result"][1] == int(finalized_block.header.slot)

@pytest.mark.asyncio
async def test_parent_block(test_client, temp_db):
    
    setup_state(GhostState.genesis(), temp_db)
    from jam.state.state import state as updated_state
    print("updated_state", updated_state.TRIE.root_hash)

    node = Node("0", "test_node", "0.0.0.0", 30333, updated_state.kappa[0], [], False, True)
    producer = BlockProducer(node, temp_db)
    # First block production
    block_1 = producer._produce_block(updated_state, TimeSlot(1))
    block_1.save(temp_db)
    setup_state(GhostState.genesis(), temp_db)
    
   #second block
    block_2 = producer._produce_block(updated_state, TimeSlot(2))
    block_2.save(temp_db)
  
    # Simulate the parent block handler
    payload = {
        "method": "parent",
        "jsonrpc": "2.0",
        "params": {},
        "id": 3
    }

    print("block_1", block_1)
    print("block_2", block_2)
    response = await test_client.post("/rpc", json=payload)
    assert response.status_code == 200
    data = await response.get_json()
    print("data",data)
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert isinstance(data["result"], list)
    assert len(data["result"]) == 2
    assert data["result"][0] == Header.__hash__(block_1.header)
    assert data["result"][1] == int(block_1.header.slot)