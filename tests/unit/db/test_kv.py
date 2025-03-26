import pytest
import os
import shutil
import tempfile
from jam.db.kv import KVStore
import json
from jam.state.state import State
from jam.network.peer import Peer
from jam.consensus.safrole.safrole import Safrole
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata
from jam.types.protocol.crypto import BandersnatchPublic, BlsPublic, Ed25519Public
from jam.types.protocol.core import ServiceId,BlobLength
from jam.types.base.sequences.bytes.bytes import Bytes
from tests.unit.db.types import DunaState

@pytest.fixture
def db_path():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_kv_store_basic_operations(db_path):
    """Test basic operations of KVStore."""
    # Initialize store
    kv = KVStore(db_path)
    
    # Test put and get
    # kv.put("State".encode(), "StateValue".encode())
    # kv.put("ServiceId".encode(), json.dumps(["PreImageKey1", "PreImageKey2"]).encode())
    # value=kv.get("ServiceId".encode())
    # valueList=json.loads(value)
    # # print("Hui",valueList[0])  
    # assert kv.get("State".encode()) == "StateValue"
    
    #State checking:
    
    # peerlist = json.load(open("genesis.json"))["peers"]
    # peers = [Peer(port=pr["port"], host=pr["host"], san=pr["id"]) for pr in peerlist]
    # validators = [ValidatorData(
    #             bandersnatch=BandersnatchPublic(pr["bandersnatch_public"]),
    #             ed25519=Ed25519Public(pr["ed25519_public"]),
    #             bls=BlsPublic(pr["bls_public"]),
    #             metadata=ValidatorMetadata(bytes(128))
    #         ) for pr in peerlist]
    # state = State.genesis(validators, Safrole.arrange_fallback(ByteArray32(bytes(32)), validators))
    # state="/genesis.json"
    genesis_file = "tests/integration/jam-duna/state_snapshots/genesis.json"
    with open(genesis_file) as file:
        genesis_data = json.loads(file.read())
        try:
            tc = DunaState.from_json(genesis_data)
            print(f"Decoded {file}")
        except Exception as e:
            print(f"❌ Failed to decode {file}: {e}")

    state1=tc.to_state()
    state1=State.transform(state1)
    state1=State.detransform(state1)
    state = tc.to_state()
    state.save(kv)
    # state=State.load(kv)    
    # blob=state.get_service_preimages(ServiceId(0),ByteArray32(0xc16326432b5b3213dfd1609495e13c6b276cb474d679645337e5c2c09f19b53c),kv)
    # print(Bytes(blob).hex())
    # Timestamp:Timestamps=state.get_service_timestamps(ServiceId(0),ByteArray32(0xc16326432b5b3213dfd1609495e13c6b276cb474d679645337e5c2c09f19b53c),BlobLength(35),kv)
    # print(Timestamp)
    keyArray=[ByteArray32(bytes.fromhex("0023000000000000478648cd19b4f812f897a26976ecf312eac28508b4368d0c")),ByteArray32(bytes.fromhex("00c1000500000000e9cd67b035be4b81c826840fd636fcbc3640d6990dfb8a6d"))]
    state2=State.load(kv,keyArray)
    print(state2.delta)
    
    
    
    
    # state.save(kv)
    
    
    # Test overwrite
    kv.put("key1".encode(), "updated_value".encode())
    assert kv.get("key1".encode()) == "updated_value".encode()
    
    # Test get non-existent key
    assert kv.get("non_existent_key".encode()) is None
    
    
    
    # Test delete
    kv.delete("key1".encode())
    assert kv.get("key1".encode()) is None

    # Close the store
    kv.close()

# def test_kv_store_multiple_operations(db_path):
#     """Test multiple operations on KVStore."""
#     kv = KVStore(db_path)
    
#     # Add multiple key-value pairs
#     test_data = {
#         "user:1": "John Doe",
#         "user:2": "Jane Smith",
#         "user:3": "Bob Johnson",
#     }
    
#     for key, value in test_data.items():
#         kv.put(key.encode(), value.encode())
    
#     # Verify all values
#     for key, expected_value in test_data.items():
#         assert kv.get(key.encode()) == expected_value
    
#     # Delete some items
#     kv.delete("user:2".encode())
#     assert kv.get("user:2".encode()) is None
#     assert kv.get("user:1".encode()) == "John Doe"  # Other keys still exist
    
#     kv.close()

# def test_kv_store_reopen(db_path):
#     """Test that data persists after closing and reopening."""
#     # Create and populate store
#     kv = KVStore(db_path)
#     kv.put("persistent_key".encode(), "persistent_value".encode())
#     kv.close()
    
#     # Reopen and check data
#     kv2 = KVStore(db_path)
#     assert kv2.get("persistent_key".encode()) == "persistent_value"
#     kv2.close()

# def test_unicode_strings(db_path):
#     """Test handling of Unicode strings."""
#     kv = KVStore(db_path)
    
#     # Various Unicode characters
#     unicode_test = {
#         "emoji": "😀🌍🚀",
#         "chinese": "你好，世界",
#         "arabic": "مرحبا بالعالم",
#         "russian": "Привет, мир",
#     }
    
#     for key, value in unicode_test.items():
#         kv.put(key.encode(), value.encode())
    
#     for key, expected_value in unicode_test.items():
#         assert kv.get(key.encode()) == expected_value
    
#     kv.close() 


