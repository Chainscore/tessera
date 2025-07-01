import json
from pathlib import Path

from tsrkit_types import Bytes

from jam.consensus.grandpa.finality import Finality
from jam.state.state import State
from jam.state.utils import construct_state_key
from jam.types import TimeSlot, HeaderHash, Block, ServiceId, AccountData
from jam.utils.dummy.dummy_block import create_dummy_block
from jam.settings import setup_setting

def get_gen_state(db_path):
	# Load genesis state
	setting = setup_setting(db_path, None)
	genesis_state_json = json.load(open(Path(__file__).parents[3] / "dev-spec.json"))["genesis_state"]
	state = State.from_keyvals(genesis_state_json, setting.state_db)
	state.store.enable_cache()
	state.store.enable_writes()
	return state, setting

def test_state_update(db_path):
	state, _ = get_gen_state(db_path)

	# Make updates
	assert state.tau == 0
	state.tau += 1
	assert state.tau == 1

	# Ensure this is just added to cache and not to DB
	assert state.store._updates[construct_state_key(11)] == TimeSlot(1).encode()
	assert state.store.get(construct_state_key(11), skip_cache=True) == TimeSlot(0).encode()


def test_block_import_state_save_n_fetch(db_path):
	state, setting = get_gen_state(db_path)
	db = setting.main_db

	parent = HeaderHash([0] * 32)
	for i in range(10):
		block = create_dummy_block()
		block.header.parent = parent
		block.header.slot = TimeSlot(i)

		# Mockup of state transition
		bh = HeaderHash(block.header.hash())
		state.tau = block.header.slot
		state.settle(bh)
		Finality.set_head(bh, db)

		block.save(db)

		# Parent for next blocks
		parent = bh

	hh_4 = db.get(Block.get_storage_key_slot(TimeSlot(4)))
	s_4 = state.load(hh_4)
	assert s_4.tau == TimeSlot(4)

def test_delta_updates(db_path):
    state, setting = get_gen_state(db_path)
    db = setting.main_db

    # Make updates
    state.delta[ServiceId(100)] = AccountData()
    assert state.delta[ServiceId(100)].service.code_hash == Bytes(32)

    state.delta[ServiceId(100)].service.code_hash = Bytes[32]([1] * 32)
    assert state.delta[ServiceId(100)].service.code_hash == Bytes([1] * 32)

    state.settle(HeaderHash([0]*32))
