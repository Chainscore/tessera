from math import floor

from tsrkit_types import TypedVector, U32

from jam.block import Block
from jam.log_setup import logger

from jam.types.protocol.core import TimeSlot

from jam.utils.shuffle import shuffle
from jam.utils.constants import (
    VALIDATOR_COUNT,
    CORE_COUNT,
    EPOCH_LENGTH,
    ROTATION_PERIOD,
)

def assign_guarantors(jam, slot: TimeSlot = None, epoch=0):
    """
    Fetch core mappings of guarantors for a specific timeslot or current state's timeslot.

    Implements Graypaper eq 11.19-11.21:
        P(e, t) = R(F([⌊C·i/V⌋ | i ∈ N_V], e), ⌊(t mod E) / R⌋)
        R(c, n) = [(x + n) mod C | x ∈ c]

    Args:
        jam: JamNode instance
        slot: A Particular Timeslot
        epoch: 0 for current epoch, -1 for previous epoch and 1 for next epoch

    Returns:
        (val_map, index_map) — core → validator data and core → validator indices
    """

    vc = VALIDATOR_COUNT

    # ------ Fetch State --------
    if slot:
        from jam.state.state import State

        ts_key = Block.get_storage_key_slot(slot)
        hh = jam.settings.main_db.get(ts_key)
        state = State.load(jam, hh)

    else:
        state = jam.state
        slot = state.tau

    # ------- Validators ---------
    if len(state.kappa) < VALIDATOR_COUNT:
        print(f"FOUND {len(state.kappa)} VALIDATORS : LESS THAN {VALIDATOR_COUNT}")
        vc = len(state.kappa)

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

    # ------- Base assignment: [⌊C·i/V⌋ | i ∈ N_V] -------
    base_assign = TypedVector[U32]([U32(floor((CORE_COUNT * i) / vc)) for i in range(vc)])

    # ------- Shuffle with epochal entropy: F(base, e) -------
    shuffled = shuffle(epoch_entropy.encode().hex(), base_assign)

    # ------- Rotation: R(c, n) = [(x + n) mod C | x ∈ c] (eq 11.19) -------
    rotation_phase = floor((slot % EPOCH_LENGTH) / ROTATION_PERIOD)
    rotated = [U32((int(x) + rotation_phase) % CORE_COUNT) for x in shuffled]

    # ------- Build mapping: core → [validator indices] -------
    index_map = {}
    val_map = {}

    for vi in range(vc):
        core = rotated[vi]
        if core not in index_map:
            index_map[core] = []
            val_map[core] = []
        index_map[core].append(vi)
        val_map[core].append(validator_set[vi])

    logger.debug("ASSIGN_G",
        eta=epoch_entropy.hex()[:16], slot=int(slot), phase=rotation_phase,
        base=[int(x) for x in base_assign[:6]],
        shuffled=[int(x) for x in shuffled[:6]],
        rotated=[int(x) for x in rotated[:6]],
        mapping={int(k): v for k, v in index_map.items()},
    )
    return val_map, index_map
