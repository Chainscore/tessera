import asyncio
from typing import Callable
from tsrkit_types import U32, U8, TypedArray, Uint

from jam.block import Block
from jam.finality.finality import Finality
from jam.types.protocol.crypto import HeaderHash, OpaqueHash
from jam.state.state import State
from jam.types.protocol.core import ServiceId
from tsrkit_types.bytes import Bytes
from jam.api.rpc.utils import parse_data
from jam.types.state.delta import AccountMetadata, LookupTable
from jam.types.protocol.core import CoreIndex
from jam.types.work.manifest import Extrinsics, Extrinsic
from jam.types.work.package import WorkPackage
from jam.network.protocols.ce_133 import WorkPackageSubmission, CE133Data, WorkPackageCore
from jam.api.rpc.parameters import parameters

Hash = TypedArray[U8]

def parameters_handler(params: list):
    return {"V1": parameters}

def service_preimage_handler(params):
    hh, sid, pi_hash = parse_data([HeaderHash, ServiceId, OpaqueHash], params)
    state_at_hh = State.load(hh)
    try:
        return list(state_at_hh.delta[sid].preimages[pi_hash])
    except Exception as e:
        return None

def best_block_handler(params: list):
    from jam.settings import settings
    best = Finality.load_latest(settings.main_db)
    return {"header_hash": list(best.header.hash()), "slot": int(best.header.slot)}

def finalized_block_handler(params: list):
    from jam.settings import settings
    final = Finality.load_final(settings.main_db)
    return {"header_hash": list(final.header.hash()), "slot": int(final.header.slot)}


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
    try:
        header_hash = parse_data([HeaderHash], params)[0]
        from jam.settings import settings
        block = Block.load(header_hash, settings.main_db)
        from jam.state.state import state
        if block.header.slot == state.tau:
            return list(state.root)
        new_slot = block.header.slot + 1
        next_block = Block.load_w_ts(new_slot, settings.main_db)
        return list(next_block.header.parent_state_root)
    except Exception as e:
        return None

def beefy_root_handler(params: list):
    hh = parse_data([HeaderHash], params)[0]
    from jam.state.state import state

    for i in state.beta.h:
        if i.header_hash == hh:
            return list(i.beefy_root)

    return None

def submit_work_package_handler(params: list):
    ci, encoded_wp, ext = parse_data([CoreIndex, Bytes, Extrinsics], params)

    wp, _ = WorkPackage.decode_from(encoded_wp)

    # TODO: fix it later
    ext = Extrinsics([Extrinsic(b"") for _ in range(len(wp.items))])

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
    "parameters": parameters_handler,
    "bestBlock": best_block_handler,
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
