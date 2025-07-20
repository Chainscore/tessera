import time

from jam.utils.constants import VALIDATOR_COUNT, CORE_COUNT, EPOCH_LENGTH, ROTATION_PERIOD, GENESIS_TS
from jam.utils.shuffle import shuffle
from tsrkit_types import TypedVector, U32
from math import floor

def rotation(c, n) -> TypedVector[U32]:
    rotated = TypedVector([])
    for x in c:
        rotated.append(U32((x+n)%CORE_COUNT))
    return rotated

def permute(e, t) -> TypedVector[U32]:
    validator_assign = TypedVector[U32]([])
    for i in range(VALIDATOR_COUNT):
        val_core = floor((CORE_COUNT * i) / VALIDATOR_COUNT)
        validator_assign.append(U32(val_core))

    c = shuffle(e.encode().hex(), validator_assign)

    n = floor((int(t) % EPOCH_LENGTH) / ROTATION_PERIOD)

    return rotation(c, n)

def guarantor_assignments(state):
    ts = (time.time() - GENESIS_TS) // 6
    n_c = permute(state.eta[2], ts)
    print("TS", ts)
    # n_c = permute(state.eta[2], state.tau)

    validator_keys = []
    for i in state.kappa:
        validator_keys.append(i.ed25519)

    mapping = {}
    for i in range(len(n_c)):
        key = n_c[i]
        value = validator_keys[i].hex()
        if key not in mapping:
            mapping[key] = set()
        mapping[key].add(value)
    print("MAPPING FN", mapping, (time.time() - GENESIS_TS) // 6, state.tau)
    return mapping
