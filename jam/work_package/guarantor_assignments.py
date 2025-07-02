from jam.utils.constants import VALIDATOR_COUNT, CORE_COUNT, EPOCH_LENGTH, ROTATION_PERIOD
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

def guarantor_assignments(eta2, tau, kappa):
    n_c = permute(eta2, tau)

    validator_keys = []
    for i in kappa:
        validator_keys.append(i.ed25519)

    mapping = {}
    for i in range(len(n_c)):
        key = n_c[i]
        value = validator_keys[i]
        if key not in mapping:
            mapping[key] = set()
        mapping[key].add(value)

    mapping = {k: mapping[k] for k in sorted(mapping.keys())}

    return mapping