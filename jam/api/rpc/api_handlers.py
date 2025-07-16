from typing import Callable, Type
from tsrkit_types import U32, U8, Bytes, Codable, TypedArray
from jam.api.rpc.utils import parse_data
from jam.consensus.grandpa.finality import Finality
from jam.state.accounts import Account, AccountDataView, StorageView
from jam.state.utils import construct_state_key
from jam.types.block.block import Block
from jam.types.protocol.crypto import HeaderHash, OpaqueHash
from jam.state.state import State, state
from jam.types.protocol.core import ServiceId, TimeSlot
from jam.types.state.delta import AccountMetadata, LookupTable

Hash = TypedArray[U8]

# RPC API Handlers 
def best_block_handler(params: list):
    from jam.settings import settings
    best = Finality.load_latest(settings.main_db)
    return list(best.header.hash()), int(best.header.slot)

def finalized_block_handler(params: list):
    from jam.settings import settings
    final = Finality.load_final(settings.main_db)
    return list(final.header.hash()), int(final.header.slot)

def parent_block_handler(params: list):
    from jam.settings import settings
    hh, = parse_data([HeaderHash], params)

    block = Block.load(hh, settings.main_db)
    if block.header.parent == Bytes[32](32):
        return None
    parent = block.load_parent(settings.main_db)
    return list(block.header.parent), int(parent.header.slot)

def state_root_handler(params: list):
    hh, = parse_data([HeaderHash], params)    
    state_at_hh = state.load(hh)
    return  list(bytes(state_at_hh.root).hex()) 

def statistics_handler(params: list):
    hh, = parse_data([HeaderHash], params)
    state_at_hh = State.load(hh)
    return  list(bytes(state_at_hh.pi.encode()).hex())

def service_data_handler(params: list):
    hh, sid = parse_data([HeaderHash, ServiceId], params)
    state_at_hh = State.load(hh)
    service_store = state_at_hh.delta[sid].service.store
    service_data = service_store.get(bytes(construct_state_key((255, sid))))
    return list(service_data)

def service_value_handler(params: list):
    hh, sid, key = parse_data([HeaderHash, ServiceId, Bytes], params)
    state_at_hh = State.load(hh)
    return list(state_at_hh.delta[sid].storage[key].hex())

def service_preimage_handler(params):
    hh, sid, pi_hash = parse_data([HeaderHash, ServiceId, OpaqueHash], params)
    state_at_hh = State.load(hh)
    return list(state_at_hh.delta[sid].preimages[pi_hash].hex())

def service_request_handler(params: list):
    hh, sid, pi_hash, pi_len = parse_data([HeaderHash, ServiceId, OpaqueHash, U32], params)
    state_at_hh = State.load(hh)
    
    return state_at_hh.delta[sid].lookup[LookupTable(hash=pi_hash, length=pi_len)]

#TODO: beefyRoot, submitPreimage, submitWorkPackage
def beefy_root_handler(params: list):
    hh = parse_data([HeaderHash], params)
    state_at_hh = State.load(hh)
    
    return []

def submit_preimage_handler(params: list):
    core_index = parse_data([U32], params)
    
    return []

def submit_work_package_handler(params: list):
    hh, sid = parse_data([HeaderHash, ServiceId], params)
    state_at_hh = State.load(hh)
    
    return []

method_map: dict[str, Callable] = {
    "bestBlock": best_block_handler,
    "finalizedBlock": finalized_block_handler,
    "parent": parent_block_handler,
    "stateRoot": state_root_handler,
    "statistics": statistics_handler,
    "serviceData" : service_data_handler,
    "serviceValue" : service_value_handler,
    "servicePreimage" : service_preimage_handler,
    "serviceRequest" : service_request_handler,
    "beefyRoot" : beefy_root_handler,
    "submitPreimage" : submit_preimage_handler,
    "submitWorkPackage": submit_work_package_handler,
}

def dispatch_api_call(method: str, params: list):
    if method not in method_map:
        raise KeyError(f"{method} call is not supported or is invalid")
    return method_map[method](params)
