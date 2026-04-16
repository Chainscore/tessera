from math import floor
from collections import deque

from tsrkit_types import TypedVector, U32

from jam.block import Block
from jam.log_setup import logger

from jam.models.protocol.core import TimeSlot

from jam.utils.shuffle import shuffle
from jam.utils.constants import (
    VALIDATOR_COUNT,
    CORE_COUNT,
    EPOCH_LENGTH,
    ROTATION_PERIOD,
)

def assign_guarantors(slot: TimeSlot = None, epoch=0):
    """
    Fetch core mappings of guarantors for a specific timeslot or current state's timeslot

    Args:
        slot: A Particular Timeslot
        epoch: 0 for current epoch, -1 for previous epoch and 1 for next epoch

    Returns:
        Mapping of core index to its assigned guarantor
    """

    vc = VALIDATOR_COUNT

    # ------ Fetch State --------
    if slot:
        from jam.settings import settings
        from jam.state.state import State

        ts_key = Block.get_storage_key_slot(slot)
        hh = settings.main_db.get(ts_key)
        from jam.state.state import State
        state = State.load(hh)

    else:
        from jam.state.state import state

        slot = state.tau

    # ------- Validators ---------
    if len(state.kappa) < VALIDATOR_COUNT:
        print(f"FOUND {len(state.kappa)} VALIDATORS : LESS THAN {VALIDATOR_COUNT}")
        vc = len(state.kappa)

    validators: TypedVector[U32] = TypedVector[U32]([U32(i) for i in range(vc)])

    # ------- Unassigned Cores -------
    validator_assign: TypedVector[U32] = TypedVector[U32]([])
    for i in range(vc):
        val_core = floor((CORE_COUNT * i) / vc)
        validator_assign.append(U32(val_core))

    # ------- Epoch Entropy -------
    if epoch == 0:
        epoch_entropy = state.eta[2]
        validator_set = state.kappa
    elif epoch == -1:
        epoch_entropy = state.eta[3]
        validator_set = state.lambda_
    elif epoch == 1:
        epoch_entropy = state.eta[1]
        validator_set = state.gamma.p
    else:
        raise ValueError("Epoch value can be 0, 1 or -1.")

    # ------- Shuffle Validators -------
    core_assign = shuffle(epoch_entropy.encode().hex(), validator_assign)

    # ------- Create Mapping ---------
    mapping = {}
    for i in range(vc):
        key = core_assign[i]
        value = validators[i]
        if key not in mapping:
            mapping[key] = set()
        mapping[key].add(value)

    # ------- Rotate Validators -------
    rotation_phase = floor((slot % EPOCH_LENGTH) / ROTATION_PERIOD)
    keys = sorted(list(mapping.keys()))
    values = [mapping[k] for k in keys]
    values = deque(values)
    values.rotate(-rotation_phase)

    index_map = {}
    val_map = {}

    for core in keys:
        for vi in values[core]:
            if core not in index_map:
                index_map[core] = []
                val_map[core] = []

            index_map[core].append(vi)
            val_map[core].append(validator_set[vi])

    logger.debug("Guarantors Mapping", state_root=state.root.hex(), tau=slot, mapping=index_map)
    return val_map, index_map
