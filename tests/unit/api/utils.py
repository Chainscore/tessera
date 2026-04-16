from pathlib import Path
from jam.finality.finality import Finality

from jam.settings import setup_setting
from jam.state.state import setup_state
from jam.block.block import Block

from tsrkit_types import Bytes, structure, TypedVector
from jam.models import BlobLength, Balance, Gas, Ai, Ao
from jam.models.protocol.core import ServiceId, TimeSlot
from jam.models.state.delta import Timestamps, LookupTable
from jam.models.protocol.crypto import StateRoot, OpaqueHash, HeaderHash
from jam.models.state.delta import AccountMetadata

def init_chain(db_path, rpc: bool = True):
    # Load genesis state
    genesis_path = Path(__file__).parents[3] / "dev-spec.json"
    settings = setup_setting(db_path, 0, "alice", 3000, rpc)
    state = setup_state(settings.state_db, str(genesis_path))

    b0 = Block.genesis()
    hh = b0.save(settings.main_db)  # Save to test-specific DB
    Finality.set_head(b0, settings.main_db)
    Finality.finalise(b0, settings.main_db)

    return state, settings, b0

def tweak_service(target_service: ServiceId, code_hash: OpaqueHash, code: bytes):
    from jam.state.state import state


    data = AccountMetadata(
        code_hash=code_hash,
        balance=Balance(1_000_000),
        gas_limit=Gas(1_000),
        min_gas=Gas(1_000),
        num_i=Ai(6),
        num_o=Ao(6),
        gratis_offset=Balance(0),
        created_at=TimeSlot(0),
        accumulated_at=TimeSlot(0),
        parent_service=ServiceId(0),
    )
    state.delta[target_service].service = data
    state.delta[target_service].preimages[code_hash] = Bytes(code)
    state.delta[target_service].lookup[
        LookupTable(hash=code_hash, length=BlobLength(len(code)))
    ] = Timestamps([state.tau])

    return data

def tweak_storage(target_service: ServiceId, code_hash: OpaqueHash, key: Bytes, val: Bytes):
    from jam.state.state import state

    data = AccountMetadata(
        code_hash=code_hash,
        balance=Balance(1_000_000),
        gas_limit=Gas(1_000),
        min_gas=Gas(1_000),
        num_i=Ai(6),
        num_o=Ao(6),
        gratis_offset=Balance(0),
        created_at=TimeSlot(0),
        accumulated_at=TimeSlot(0),
        parent_service=ServiceId(0),
    )
    state.delta[target_service].service = data
    state.delta[target_service].storage[key] = val

    return data

def tweak_lookup(target_service: ServiceId, code_hash: OpaqueHash, code: bytes):
    from jam.state.state import state

    data = AccountMetadata(
        code_hash=code_hash,
        balance=Balance(1_000_000),
        gas_limit=Gas(1_000),
        min_gas=Gas(1_000),
        num_i=Ai(6),
        num_o=Ao(6),
        gratis_offset=Balance(0),
        created_at=TimeSlot(0),
        accumulated_at=TimeSlot(0),
        parent_service=ServiceId(0),
    )
    state.delta[target_service].service = data
    state.delta[target_service].lookup[
        LookupTable(hash=code_hash, length=BlobLength(len(code)))
    ] = Timestamps([])

    state.delta[target_service].lookup[
        LookupTable(hash=code_hash, length=BlobLength(len(code)))
    ] = Timestamps([TimeSlot(1)])

    state.delta[target_service].lookup[
        LookupTable(hash=code_hash, length=BlobLength(len(code)))
    ] = Timestamps([TimeSlot(1), TimeSlot(3)])

    state.delta[target_service].lookup[
        LookupTable(hash=code_hash, length=BlobLength(len(code)))
    ] = Timestamps([TimeSlot(1), TimeSlot(3), TimeSlot(5)])

    return data

@structure
class TestVector:
    block: Block
    state_root: StateRoot
    header_hash: HeaderHash

Vectors = TypedVector[TestVector]

def produce_chain(db_path, init: bool = True, rpc: bool = True):
    """
    Produce chain of 5 blocks and save in db.
    Returns latest state and node settings
    """
    from jam.settings import settings

    if init:
        state, settings, b0 = init_chain(db_path, rpc)
    else:
        from jam.state.state import state

        b0 = Finality.load_final(settings.main_db)

    b1 = b0.produce(TimeSlot(1), state)
    state._force_transition(b1)

    settings.clear()

    settings = setup_setting(db_path, 3, "dave", 3000, rpc)
    state.store._DB = settings.state_db

    b2 = b1.produce(TimeSlot(2), state)
    state._force_transition(b2)

    b3 = b2.produce(TimeSlot(3), state)
    state._force_transition(b3)

    settings.clear()

    settings = setup_setting(db_path, 5, "fergie", 3000, rpc)
    state.store._DB = settings.state_db

    b4 = b3.produce(TimeSlot(4), state)
    state._force_transition(b4)

    settings.clear()

    settings = setup_setting(db_path, 2, "charlie", 3000, rpc)
    state.store._DB = settings.state_db

    b5 = b4.produce(TimeSlot(5), state)
    state._force_transition(b5)

    return state, settings