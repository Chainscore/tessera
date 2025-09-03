import asyncio
from typing import Callable
from tsrkit_types import U32, U8, Bytes, TypedArray, Null, Uint

from jam.api.rpc.broker import broker
from jam.block import Block
from jam.finality.finality import Finality
from jam.settings import settings
from jam.types.protocol.crypto import HeaderHash, OpaqueHash
from jam.state.state import State
from jam.types.protocol.core import ServiceId
from tsrkit_types.bytes import Bytes
from jam.api.rpc.utils import parse_data
from jam.types.state.delta import AccountMetadata, LookupTable
from jam.utils.merkle import MMRFunctions
from jam.types.protocol.core import CoreIndex
from jam.types.work.manifest import Extrinsics, Extrinsic
from jam.types.work.package import WorkPackage
from jam.network.protocols.ce_133 import WorkPackageSubmission, CE133Data, WorkPackageCore

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
            "max_accumulate_gas": 1000000,
            "max_is_authorized_gas": 50000000,
            "max_refine_gas": 100000000,
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
        return list(state_at_hh.delta[sid].preimages[pi_hash])
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
    print("subscribeServiceRequest called", pi_hash.hex())
    try:
        value = list(state_at_hh.delta[sid].preimages[pi_hash])
    except Exception:
        value = None

    method = f"subscribeServiceRequest:{sid}:{list(pi_hash)}:{pi_len}:{finality}"

    await broker.publish(method, {"header_hash": list(block.header.hash()), "slot": int(block.header.slot), "value": value})

def service_data_handler(params):
    hh, sid = parse_data([HeaderHash, ServiceId], params)
    state_at_hh = State.load(hh)
    try:
        service = state_at_hh.delta[sid].service
        accountMetadata = AccountMetadata(
            code_hash=service.code_hash,
            balance=service.balance,
            gas_limit=service.gas_limit,
            min_gas=service.min_gas,
            num_i=service.num_i,
            num_o=service.num_o,
            gratis_offset=service.gratis_offset,
            created_at=service.created_at,
            accumulated_at=service.accumulated_at,
            parent_service=service.parent_service
        )

        return list(accountMetadata.encode())
    except Exception as e:
        return None

def submit_preimage_handler(params):
    sid, code = parse_data([ServiceId, Bytes], params)
    from jam.block.extrinsics.preimages import preimg_store, Preimage

    pre_img = Preimage(requester=ServiceId(sid), blob=Bytes(code))
    preimg_store.store(pre_img)

def state_root_handler(params: list):
    hh = parse_data([HeaderHash], params)

    from jam.settings import settings
    block = Block.load(hh[0], settings.main_db)
    new_slot = block.header.slot + 1
    next_block = Block.load_w_ts(new_slot, settings.main_db)
    return list(next_block.header.parent_state_root)

def beefy_root_handler(params: list):
    hh = parse_data([HeaderHash], params)[0]
    from jam.state.state import state

    for i in state.beta.h:
        if i.header_hash == hh:
            return list(i.beefy_root)

    return None

def finalized_block_handler(params: list):
    from jam.settings import settings

    final = Finality.load_final(settings.main_db)
    return {"header_hash": list(final.header.hash()), "slot": int(final.header.slot)}

def submit_work_package_handler(params: list):
    ci, encoded_wp, ext = parse_data([CoreIndex, Bytes, Extrinsics], params)

    wp, _ = WorkPackage.decode_from(encoded_wp)

    print("Received work package", wp.to_json())
    print("Received core index", ci)
    print("Received extrinsics", ext)

    # TODO: fix it later
    ext = Extrinsics([Extrinsic(b"") for i in range(len(wp.items))])

    CE133 = WorkPackageSubmission()
    wc = WorkPackageCore(wp, ci)
    package_len = Uint[32](len(wc.encode()))
    ext_len = Uint[32](len(ext.encode()))
    data = CE133Data(
        package_len=package_len, package_data=wc, extrinsics_len=ext_len, extrinsics=ext
    )
    responses = asyncio.create_task(CE133.transmit(data))

def service_request_handler(params: list):
    try:
        hh, sid, pi_hash, pi_len = parse_data(
            [HeaderHash, ServiceId, OpaqueHash, U32], params
        )
        state_at_hh = State.load(hh)

        return list(state_at_hh.delta[sid].lookup[LookupTable(hash=pi_hash, length=pi_len)])
    except Exception as e:
        return None


method_map: dict[str, Callable] = {
    "parameters": parameters,
    "bestBlock": best_block,
    "servicePreimage": service_preimage_handler,
    "serviceData": service_data_handler,
    "submitPreimage": submit_preimage_handler,
    "stateRoot": state_root_handler,
    "beefyRoot": beefy_root_handler,
    "finalizedBlock": finalized_block_handler,
    "submitWorkPackage": submit_work_package_handler,
    "serviceRequest": service_request_handler,
}


def dispatch_ws_call(method: str, params: list):
    if method not in method_map:
        raise KeyError(f"{method} call is not supported or is invalid")
    return method_map[method](params)
