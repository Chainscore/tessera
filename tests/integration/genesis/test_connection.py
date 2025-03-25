import asyncio
import json
import os
import pytest
import shutil
import tempfile
from pathlib import Path

from jam.chainspec import chain_config
from jam.consensus.safrole.safrole import Safrole
from jam.db.kv import KVStore
from jam.network.node import Node
from jam.network.peer import Peer
from jam.network.dummy_bp import block_producer
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint
from jam.state.state import State
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.protocol.crypto import BandersnatchPublic, BlsPublic, Ed25519Public
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jam.types.block import Block

# Skip these tests if we're not running integration tests
pytestmark = pytest.mark.integration

@pytest.fixture
async def temp_directory():
    """Provide a temporary directory for test data"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
async def node_setup(temp_directory):
    """Setup function for creating a single node"""
    async def _setup_node(port, peer_ports):
        db_path = f"{temp_directory}/db_{port}"
        
        # Create genesis configuration
        peers = []
        for p in peer_ports:
            peers.append({
                "port": p,
                "host": "127.0.0.1",
                "id": f"node_{p}",
                "bandersnatch_public": f"0x{os.urandom(32).hex()}",
                "ed25519_public": f"0x{os.urandom(32).hex()}",
                "bls_public": f"0x{os.urandom(144).hex()}"
            })
        
        # Create genesis file
        genesis_path = f"{temp_directory}/genesis_{port}.json"
        with open(genesis_path, 'w') as f:
            json.dump({"peers": peers}, f)
        
        # Create key files directory
        os.makedirs(f"seeds/{port}", exist_ok=True)
        
        # Create dummy keys
        keys = {
            str(port): {
                "ed25519_private": f"0x{os.urandom(32).hex()}",
                "bandersnatch_private": f"0x{os.urandom(32).hex()}"
            }
        }
        with open(f"seeds/keys.json", 'w') as f:
            json.dump(keys, f)
        
        # Load validator data from seeds
        ed25519_public = Ed25519PrivateKey.from_private_bytes(
                            bytes.fromhex(keys[str(port)]["ed25519_private"][2:])
                        ).public_key()

        bandersnatch_private = int.from_bytes(bytes.fromhex(keys[str(port)]["bandersnatch_private"][2:]), 'little')
        bandersnatch_public = BandersnatchPublic((BandersnatchPoint.generator_point() * bandersnatch_private).point_to_string().hex())
        
        # Create peer objects
        peer_objs = [Peer(port=p, host="127.0.0.1", san=f"node_{p}") for p in peer_ports]
        
        # Create validator data
        my_data = ValidatorData(
            bandersnatch=bandersnatch_public,
            ed25519=ed25519_public,
            bls=BlsPublic(bytes(144)),
            metadata=ValidatorMetadata(bytes(128))
        )
        
        # Create node
        node = Node(
            node_id=port,
            node_name=f"node_{port}",
            host="127.0.0.1",
            port=port,
            peers=peer_objs,
            validator_data=my_data
        )
        
        # Create db
        db = KVStore(db_path)
        
        # Initialize state from genesis
        genesis_vals = [ValidatorData(
            bandersnatch=BandersnatchPublic(pr["bandersnatch_public"]),
            ed25519=Ed25519Public(pr["ed25519_public"]),
            bls=BlsPublic(pr["bls_public"]),
            metadata=ValidatorMetadata(bytes(128))
        ) for pr in peers]
        
        state = State.genesis(genesis_vals, Safrole.arrange_fallback(ByteArray32(bytes(32)), genesis_vals))
        state.save(db)
        
        return node, db, genesis_path
    
    yield _setup_node
    
    # Cleanup seed directories after the test
    for item in os.listdir("seeds"):
        try:
            if item.isdigit() or os.path.isdir(os.path.join("seeds", item)):
                shutil.rmtree(os.path.join("seeds", item))
        except:
            pass

@pytest.fixture
async def network(node_setup):
    """Setup a network of multiple nodes"""
    ports = [30334, 30335, 30336]
    
    # Create nodes
    node_configs = []
    for port in ports:
        peer_ports = [p for p in ports if p != port]
        node, db, genesis_path = await node_setup(port, peer_ports)
        node_configs.append((node, db, genesis_path))
    
    # Start all nodes
    node_tasks = []
    async with asyncio.TaskGroup() as tg:
        for node, _, _ in node_configs:
            task = tg.create_task(node.initialize())
            node_tasks.append(task)
        
        # Wait for initialization
        await asyncio.sleep(5)
    
    yield node_configs
    
    # Cleanup connections
    for node, _, _ in node_configs:
        if hasattr(node, 'server') and node.server:
            node.server.close()
            await node.server.wait_closed()

@pytest.mark.asyncio
async def test_block_production(network):
    """Test the full flow from node initialization to block production and propagation"""
    try:
        # Run block producers for a short period
        async with asyncio.TaskGroup() as tg:
            # Start block producers for each node
            for node, db, _ in network:
                tg.create_task(block_producer(node, db))
            
            # Let the system run for a bit
            async def end_after_timeout():
                await asyncio.sleep(15)
                return
            
            tg.create_task(end_after_timeout())
        
        # Check state after running
        for node, db, _ in network:
            state = State.load(db)
            assert state is not None, "State should be loaded successfully"
            # Add more assertions here based on expected state changes
    
    except Exception as e:
        pytest.fail(f"Test failed with error: {e}")

@pytest.mark.asyncio
async def test_direct_message_exchange(network):
    """Test direct message exchange between nodes using QUIC protocol"""
    try:
        # Ensure all nodes are connected
        connected = all(len(node.connections) > 0 for node, _, _ in network)
        assert connected, "Not all nodes have established connections"
        
        # Get first two nodes for testing
        node1, db1, _ = network[0]
        node2, db2, _ = network[1]
        
        # Create a test message
        test_message = json.dumps({
            "type": "test_message",
            "content": "Hello from node1",
            "timestamp": str(asyncio.get_event_loop().time())
        }).encode()
        
        # Capture received messages
        received_messages = []
        
        # Override the quic_event_received in the second node's connections to capture messages
        original_event_received = node2.connections[0].quic_event_received
        
        async def capture_message(event):
            from aioquic.quic.events import StreamDataReceived
            if isinstance(event, StreamDataReceived):
                received_messages.append(event.data)
            await original_event_received(event)
        
        node2.connections[0].quic_event_received = capture_message
        
        # Send a message from node1 to node2
        for client in node1.connections:
            await client.send_message(test_message)
        
        # Wait for message propagation
        await asyncio.sleep(2)
        
        # Check if the message was received
        assert len(received_messages) > 0, "No messages were received"
        assert any(test_message in msg for msg in received_messages), "Test message not received"
        
    except Exception as e:
        pytest.fail(f"Test failed with error: {e}")

@pytest.mark.asyncio
async def test_block_propagation(network):
    """Test that blocks are properly propagated across the network"""
    try:
        # Create a dummy block
        from tests.fixtures.dummy_block import create_dummy_block
        test_block = create_dummy_block()
        
        # Create a collection to track received blocks
        received_blocks = []
        
        # Get first node to broadcast the block
        sender_node, _, _ = network[0]
        
        # Override quic_event_received in other nodes to track block reception
        for i in range(1, len(network)):
            node, _, _ = network[i]
            for client in node.connections:
                original_handler = client.quic_event_received
                
                async def block_capture(event):
                    from aioquic.quic.events import StreamDataReceived
                    if isinstance(event, StreamDataReceived):
                        try:
                            block = Block.decode_from(event.data)
                            received_blocks.append(block)
                        except:
                            pass  # Not a block
                    await original_handler(event)
                
                client.quic_event_received = block_capture
        
        # Send the block from the first node
        for client in sender_node.connections:
            await client.send_message(test_block.encode())
        
        # Wait for block propagation
        await asyncio.sleep(3)
        
        # Verify blocks were received
        assert len(received_blocks) > 0, "No blocks were received by other nodes"
        
        # Verify block contents match what was sent
        for block in received_blocks:
            assert block.header.hash() == test_block.header.hash(), "Received block hash doesn't match sent block"
        
    except Exception as e:
        pytest.fail(f"Test failed with error: {e}")
