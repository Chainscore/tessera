import pytest
from jam.settings import setup_setting
from jam.api.rpc.app import rpc
from jam.state.state import setup_state
from jam.block import Block
from jam.finality.finality import Finality
from jam.network.node import Node
from jam.types.protocol.core import TimeSlot


# @pytest.mark.asyncio
# async def test_best_block(db_path):
#     settings = setup_setting(db_path, 0, "alice", 0)
#     state = setup_state(settings.state_db)
#
#     block = Block.genesis()
#     hh = block.save(settings.main_db)  # Save to test-specific DB
#     Finality.finalise(hh, settings.main_db)
#     Finality.set_head(hh, settings.main_db)
#
#     b1 = BlockProducer(node=Node("", "", 0, settings.val, [], False, False), db=settings.main_db)._produce_block(state, TimeSlot(1))
#     state.transition(b1)
#
#     # Simulate the best block handler
#     payload = {
#         "method": "bestBlock",
#         "jsonrpc": "2.0",
#         "params": [],
#         "id": 3
#     }
#
#     response = await rpc.test_client().post("/rpc", json=payload)
#     assert response.status_code == 200
#     data = await response.get_json()
#     assert data["jsonrpc"] == "2.0"
#     assert data["id"] == 3
#     assert isinstance(data["result"], list)
#     assert len(data["result"]) == 2
#     assert data["result"][0] == list(b1.header.hash())
#     assert data["result"][1] == int(b1.header.slot)

# @pytest.mark.asyncio
# async def test_finalized_block(test_client, temp_db):
#     # Simulate the finalized block
#     # Create a block and finalize it
#     block = Block.from_random()
#     Finality.finalise(block.header.slot, temp_db)
#     block.save(temp_db)
#     
#     # Load the finalized block to check the finality
#     finalized_block = Finality.load_final(temp_db)
#     # Simulate the finalized block handler
#     payload = {
#         "method": "finalizedBlock",
#         "jsonrpc": "2.0",
#         "params": {},
#         "id": 3
#     }
#
#     response = await test_client.post("/rpc", json=payload)
#     assert response.status_code == 200
#     data = await response.get_json()
#     assert data["jsonrpc"] == "2.0"
#     assert data["id"] == 3
#     assert isinstance(data["result"], list)
#     assert len(data["result"]) == 2
#     assert data["result"][0] == Header.__hash__(finalized_block.header)
#     assert data["result"][1] == int(finalized_block.header.slot)
#
# @pytest.mark.asyncio
# async def test_parent_block(test_client, temp_db):
#     
#     setup_state(GhostState.genesis(), temp_db)
#     from jam.state.state import state as updated_state
#
#     node = Node("0", "test_node", "0.0.0.0", 30333, updated_state.kappa[0], [], False, True)
#     producer = BlockProducer(node, temp_db)
#     # First block production
#     block_1 = producer._produce_block(updated_state, TimeSlot(1))
#     block_1.save(temp_db)
#     updated_state.tau = TimeSlot(1)
#     
#    #second block
#     block_2 = producer._produce_block(updated_state, TimeSlot(2))
#     block_2.save(temp_db)
#     updated_state.tau = TimeSlot(2)
#
#   
#     # Simulate the parent block handler
#     payload = {
#         "method": "parent",
#         "jsonrpc": "2.0",
#         "params": {
#             "Hash": Header.__hash__(block_2.header),
#         },
#         "id": 3
#     }
#     response = await test_client.post("/rpc", json=payload)
#     assert response.status_code == 200
#     data = await response.get_json()
#     assert data["jsonrpc"] == "2.0"
#     assert data["id"] == 3
#     assert isinstance(data["result"], list)
#     assert len(data["result"]) == 2
#     assert data["result"][0] == Header.__hash__(block_1.header)
#     assert data["result"][1] == int(block_1.header.slot)
#
# @pytest.mark.asyncio
# async def test_state_root(test_client, temp_db):
#     
#     setup_state(GhostState.genesis(), temp_db)
#     from jam.state.state import state as updated_state
#     block = Block.from_random()
#
#       # Simulate the state root handler
#     payload = {
#         "method": "stateRoot",
#         "jsonrpc": "2.0",
#         "params": {
#             "Hash": Header.__hash__(block.header),
#         },
#         "id": 3
#     }
#     response = await test_client.post("/rpc", json=payload)
#     assert response.status_code == 200
#     data = await response.get_json()
#     assert data["jsonrpc"] == "2.0"
#     assert data["id"] == 3
#     assert isinstance(data["result"], list)
#     assert len(data["result"]) == 1
#     assert data["result"][0] == bytes(state.root).hex()
#
#
# @pytest.mark.asyncio
# async def test_statistics(test_client, temp_db):
#
#     setup_state(GhostState.genesis(), temp_db)
#     from jam.state.state import state as updated_state
#
#     block = Block.from_random()
#
#     # Simulate the statistics handler
#     payload = {
#         "method": "statistics",
#         "jsonrpc": "2.0",
#         "params": {
#             "Hash" : Header.__hash__(block.header)
#         },
#         "id": 3
#     }
#
#     response = await test_client.post("/rpc", json=payload)
#     assert response.status_code == 200
#     data = await response.get_json()
#     assert data["jsonrpc"] == "2.0"
#     assert data["id"] == 3
#     assert data["result"][0] == str(updated_state.pi)
#
#
# @pytest.mark.asyncio
# async def test_service_data(test_client, temp_db):
#     from jam.state.state import state
#
# #   Dummy account data
#     dummy_account = AccountData(
#         code_hash=ServiceCodeHash(b'\x00' * 32),
#         balance=Balance(1000),
#         gas_limit=Gas(100000),
#         min_gas=Gas(100),
#         num_o=Ao(1),
#         num_i=Ai(2)
#     )
#     service_id = ServiceId(33)
#     state.delta[service_id] = dummy_account
#
#     # Fetch to verify
#     account = state.delta[service_id]
#
#     # Simulate the service data handler
#     payload = {
#         "method": "serviceData",
#         "jsonrpc": "2.0",
#         "params": {
#             "Hash": Header.__hash__(dummy_account),
#             "ServiceId": 33
#         },
#         "id": 3
#     }
#     response = await test_client.post("/rpc", json=payload)
#     assert response.status_code == 200
#     data = await response.get_json()
#     assert data["jsonrpc"] == "2.0"
#     assert data["id"] == 3
#     assert isinstance(data["result"], list)
#     assert len(data["result"]) == 1
#     assert data["result"][0] == str(state.delta[ServiceId(33)].data)
#
#
# @pytest.mark.asyncio
# async def test_service_value(test_client, temp_db):
#     from jam.state.state import state
#     
#     dummy_account = AccountData(
#         code_hash=ServiceCodeHash(b'\x00' * 32),
#         balance=Balance(1000),
#         gas_limit=Gas(100000),
#         min_gas=Gas(100),
#         num_o=Ao(1),
#         num_i=Ai(2)
#     )
#     service_id = ServiceId(42)
#     state.delta[service_id] = dummy_account  # <-- Set before handler call
#
#     block = Block.from_random()
#
#  # Choose a service ID (must be ServiceId type, not int)
#     storage = StorageView(service_id, temp_db, state.TRIE)
#
#     # Create a dummy key and value
#     key = ByteArray32(b'\x01' * 32)
#     value = Bytes(b"hello world")
#
#     # Set the value in storage
#     storage[key] = value
#
#     # Retrieve the value
#     retrieved = bytes(storage[key])
#     
#     # Simulate the service value handler
#     payload = {
#         "method": "serviceValue",
#         "jsonrpc": "2.0",
#         "params": {
#             "Hash": Header.__hash__(block.header),
#             "ServiceId": 42,
#             "Blob": str(ByteArray32(b'\x01' * 32))
#         },
#         "id": 3
#     }
#     response = await test_client.post("/rpc", json=payload)
#     assert response.status_code == 200
#     data = await response.get_json()
#     assert data["jsonrpc"] == "2.0"
#     assert data["id"] == 3
#     assert len(data["result"]) == 1
#     assert data["result"][0] == str(retrieved)
#
#
# @pytest.mark.asyncio
# async def test_service_preimage(test_client, temp_db):
#     from jam.state.state import state
#
#     dummy_account = AccountData(
#         code_hash=ServiceCodeHash(b'\x00' * 32),
#         balance=Balance(1000),
#         gas_limit=Gas(100000),
#         min_gas=Gas(100),
#         num_o=Ao(1),
#         num_i=Ai(2)
#     )
#     service_id = ServiceId(42)
#     state.delta[service_id] = dummy_account 
#
#     block = Block.from_random()
#
#     # Initialize the preimage view
#     preimage = PreImageView(service_id, temp_db, state.TRIE)
#
#     # Create a dummy key and value
#     key = ByteArray32(b'\x01' * 32)
#     value = Bytes(b"hello world")
#
#     # Set the value in storage
#     preimage[key] = value
#
#     # Retrieve the value
#     retrieved = bytes(preimage[key])
#     
#     # Simulate the service preimage handler
#     payload = {
#         "method": "servicePreimage",
#         "jsonrpc": "2.0",
#         "params": {
#             "Hash": Header.__hash__(block.header),
#             "ServiceId": 42,
#             "Blob": str(ByteArray32(b'\x01' * 32))
#         },
#         "id": 3
#     }
#     response = await test_client.post("/rpc", json=payload)
#     assert response.status_code == 200
#     data = await response.get_json()
#     assert data["jsonrpc"] == "2.0"
#     assert data["id"] == 3
#     assert len(data["result"]) == 1
#     assert data["result"][0] == str(retrieved)
#
# @pytest.mark.asyncio
# async def test_service_request(test_client, temp_db):
#     from jam.state.state import state
#
#     dummy_account = AccountData(
#         code_hash=ServiceCodeHash(b'\x00' * 32),
#         balance=Balance(1000),
#         gas_limit=Gas(100000),
#         min_gas=Gas(100),
#         num_o=Ao(1),
#         num_i=Ai(2)
#     )
#     service_id = ServiceId(42)
#     state.delta[service_id] = dummy_account
#
#     block = Block.from_random()
#
#  
#     timestamps = TimestampsView(service_id, temp_db, state.TRIE)
#     hash_bytes = ByteArray32(b'\x01' * 32)
#     length = 2
#     lookup_key = LookupTable(hash_bytes, U32(length))
#     dummy_timestamps = Timestamps([U32(123456789), U32(987654321)])
#     timestamps[lookup_key] = dummy_timestamps
#
#     retrieved = timestamps[lookup_key]
#     print(f"Retrieved value: {retrieved}")
#     # Simulate the service request handler
#     payload = {
#         "method": "serviceRequest",
#         "jsonrpc": "2.0",
#         "params": {
#             "Hash": Header.__hash__(block.header),
#             "ServiceId": 42,
#             "hash": str(hash_bytes),
#             "u32": int(length)
#         },
#         "id": 3
#     }
#     
#     response = await test_client.post("/rpc", json=payload)
#     assert response.status_code == 200
#     data = await response.get_json()
#     assert data["jsonrpc"] == "2.0"
#     assert data["id"] == 3
#     assert len(data["result"]) == 1
#     assert data["result"][0] == str(retrieved)
