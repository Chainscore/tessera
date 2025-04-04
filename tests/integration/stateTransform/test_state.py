import pytest
import os
import shutil
import tempfile
import pickle

import json

from jam.db.kv import KVStore
from jam.state.state import State
from jam.network.peer import Peer
from jam.consensus.safrole.safrole import Safrole
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata
from jam.types.protocol.crypto import BandersnatchPublic, BlsPublic, Ed25519Public
from jam.types.protocol.core import ServiceId,BlobLength
from jam.types.base.sequences.bytes.bytes import Bytes
from tests.integration.stateTransform.types import DunaState
from jam.state.merkle.merkle import StateMerkle

@pytest.fixture
def db_path():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def get_cached_tree(db: KVStore) -> dict:
    """
    Retrieve the entire update tree from RocksDB.
    The tree is stored under the key b"cached_tree" as a serialized dictionary.
    Returns:
        dict: Mapping of node keys (e.g., node hashes) to encoded node data.
    """
    tree_bytes = db.get(b"cached_tree:")
    
    if tree_bytes is not None:
        return pickle.loads(tree_bytes)
    return {}

def test_state_transform(db_path):
    """Test basic operations of KVStore."""
    # Initialize store
    kv = KVStore(db_path)
    
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
    
    keyArray=[ByteArray32(bytes.fromhex("0023000000000000478648cd19b4f812f897a26976ecf312eac28508b4368d0c")),ByteArray32(bytes.fromhex("00c1000500000000e9cd67b035be4b81c826840fd636fcbc3640d6990dfb8a6d")),ByteArray32(bytes.fromhex("00fe00ff00ff00ff6326432b5b3213dfd1609495e13c6b276cb474d679645337")),ByteArray32(bytes.fromhex("00fe00ff00ff00ffed2fda1ccc4b59d6b382edb3dcd2a312925839a006199060"))]
    # keyArray=[ByteArray32(bytes.fromhex("0023000000000000478648cd19b4f812f897a26976ecf312eac28508b4368d0c"))]
    state2=State.load(kv,keyArray)
    # Checking the delta of JamDuna and our U32[0] related data from our DB is same
    assert(state1.delta==state2.delta)

    # merkle = StateMerkle()
    # cached_tree = get_cached_tree(db=kv)
    # print(state.get_merkle_nodes())
    # root,updated_tree=merkle.merkelize(state.transform(),cached_tree)
    # root,tree = merkle.merkelize(state.transform(),cached_tree)
    print(get_cached_tree(db=kv))

    # Close the store
    kv.close()
