from typing import Callable
from tsrkit_types import U32, U8, Bytes, TypedArray, Null

from jam.api.rpc.broker import broker
from jam.finality.finality import Finality
from jam.types.protocol.crypto import HeaderHash, OpaqueHash
from jam.state.state import State
from jam.types.protocol.core import ServiceId
from tsrkit_types.bytes import Bytes
from jam.api.rpc.utils import parse_data

Hash = TypedArray[U8]

def parameters(params: list):
    return {
        "V1": {
            "deposit_per_item": 10,
            "deposit_per_byte": 1,
            "deposit_per_account": 100,
            "core_count": 2,
            "min_turnaround_period": 19200,
            "epoch_period": 12,
            "max_accumulate_gas": 10000000,
            "max_is_authorized_gas": 50000000,
            "max_refine_gas": 1000000000,
            "block_gas_limit": 20000000,
            "recent_block_count": 8,
            "max_work_items": 16,
            "max_dependencies": 8,
            "max_tickets_per_block": 3,
            "max_lookup_anchor_age": 14400,
            "tickets_attempts_number": 3,
            "auth_window": 8,
            "slot_period_sec": 6,
            "auth_queue_len": 80,
            "rotation_period": 4,
            "max_extrinsics": 128,
            "availability_timeout": 5,
            "val_count": 6,
            "max_authorizer_code_size": 64000,
            "max_input": 13794305,
            "max_service_code_size": 4000000,
            "basic_piece_len": 4,
            "max_imports": 3072,
            "segment_piece_count": 1026,
            "max_report_elective_data": 49152,
            "transfer_memo_size": 128,
            "max_exports": 3072,
            "epoch_tail_start": 10
        }
    }

def service_preimage_handler(params):
    hh, sid, pi_hash = parse_data([HeaderHash, ServiceId, OpaqueHash], params)
    state_at_hh = State.load(hh)
    try:
        return {"result": list(state_at_hh.delta[sid].preimages[pi_hash].hex())}
    except Exception as e:
        return None

def best_block(params: list):
    from jam.settings import settings
    best = Finality.load_final(settings.main_db)
    return {"header_hash": list(best.header.hash()), "slot": int(best.header.slot)}

async def initial_subscribe_service_request(sid, pi_hash, pi_len, finality):
    from jam.settings import settings
    # block = Finality.load_final(settings.main_db) if finality else Finality.load_latest(settings.main_db)
    block = Finality.load_final(settings.main_db)
    state_at_hh = State.load(block.header.hash())
    try:
        value = list(state_at_hh.delta[sid].preimages[pi_hash].hex())
    except Exception:
        value = []

    method = f"subscribeServiceRequest:{sid}:{list(pi_hash)}:{pi_len}:{finality}"

    await broker.publish(method, {"header_hash": list(block.header.hash()), "slot": int(block.header.slot), "value": value})

def service_data_handler(params):
    hh, sid = parse_data([HeaderHash, ServiceId], params)
    state_at_hh = State.load(hh)
    try:
        return {"result": list(state_at_hh.delta[sid].hex())}
    except Exception as e:
        return None

def submit_preimage_handler(params):
    sid, code = parse_data([ServiceId, Bytes], params)
    from jam.block.extrinsics.preimages import preimg_store, Preimage

    pre_img = Preimage(requester=ServiceId(sid), blob=Bytes(code))
    preimg_store.store(pre_img)


method_map: dict[str, Callable] = {
    "parameters": parameters,
    "bestBlock": best_block,
    "servicePreimage": service_preimage_handler,
    "serviceData": service_data_handler,
    "submitPreimage": submit_preimage_handler,
}


def dispatch_ws_call(method: str, params: list):
    if method not in method_map:
        raise KeyError(f"{method} call is not supported or is invalid")
    return method_map[method](params)
