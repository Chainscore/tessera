from typing import Dict, List

from tsrkit_types.sequences import TypedVector
from tsrkit_types.integers import U32

from jam.models import OpaqueHash, ValidatorIndex, Sigma
from jam.models import OpaqueHash, ValidatorIndex, Sigma, ValidatorData
from jam.models.protocol.core import CoreIndex, TimeSlot

from jam.utils.constants import (
    VALIDATOR_COUNT,
    CORE_COUNT,
    EPOCH_LENGTH,
    ROTATION_PERIOD,
)
from math import floor
from jam.utils.shuffle import shuffle
from collections import deque

ValidatorList = TypedVector[ValidatorIndex]

def guarantor_assignment(
    eta, kappa, lambda_, gamma_p, block_slot, report_slot, tau
) -> Dict[CoreIndex, List]:
    """
    Description:
        In this given function take some entropy according to epoch and slot and create mapping between core and validator.

    Args :
        eta: define as entropy
        kappa:  help to get current validator data
        lambda_: help to get the previous validator data
        gamma_p: gamma.p
        block_slot: through this we get the current block's slot
        report_slot: slot assigned to the work report
        tau: state timeslot

    Return:
        It's return the dict that is mapping between core and validator

    """
    # ------- Validator order ---------
    array_validator = TypedVector[U32]([])
    for i in range(VALIDATOR_COUNT):
        array_validator.append(U32(i))

    # ------- Validator assignment to the cores -------
    validator_assign = TypedVector[U32]([])
    for i in range(VALIDATOR_COUNT):
        val_core = floor((CORE_COUNT * i) / VALIDATOR_COUNT)
        validator_assign.append(U32(val_core))

    epoch_change = (int(tau) // EPOCH_LENGTH) < (int(block_slot) // EPOCH_LENGTH)
    eta2_post = eta[1] if epoch_change else eta[2]
    eta3_post = eta[2] if epoch_change else eta[3]

    kappa_post = gamma_p if epoch_change else kappa
    lambda_post = kappa if epoch_change else lambda_

    # <------------- Entropy for current epoch ------------------>
    epoch_entropy = None
    validator_keys = []
    if report_slot == block_slot:
        epoch_entropy = eta2_post
        for i in kappa_post:
            validator_keys.append(i.ed25519)

    # <------------- Entropy for previous rotation in same epoc ------------------>
    if report_slot != block_slot and floor(
        (int(block_slot) - ROTATION_PERIOD) / EPOCH_LENGTH
    ) == floor(int(block_slot) / EPOCH_LENGTH):
        epoch_entropy = eta2_post
        for i in kappa_post:
            validator_keys.append(i.ed25519)

    # <------------- Entropy for previous rotation but in last epoch ------------------>
    if report_slot != block_slot and floor(
        (int(block_slot) - ROTATION_PERIOD) / EPOCH_LENGTH
    ) != floor(int(block_slot) / EPOCH_LENGTH):
        epoch_entropy = eta3_post
        for i in lambda_post:
            validator_keys.append(i.ed25519)

    # ------- Shuffle validator with respect to the given entropy -------
    core_assign = shuffle(epoch_entropy.encode().hex(), validator_assign)

    # an empty dictionary to store the mapping between core and validator
    mapping = {}
    for i in range(len(array_validator)):
        key = core_assign[i]
        value = array_validator[i]
        if key not in mapping:
            mapping[key] = set()
        mapping[key].add(value)
    mapping = {k: mapping[k] for k in sorted(mapping.keys())}

    # rotation phase (number of rotation between cores)
    work_report_slot = report_slot
    rotation_phase = floor((int(work_report_slot) % EPOCH_LENGTH) / ROTATION_PERIOD)
    keys = list(mapping.keys())
    values = [mapping[k] for k in keys]
    values = deque(values)
    values.rotate(-rotation_phase)

    mapping = {keys[i]: values[i] for i in range(len(keys))}

    return mapping

def rotation_fn(c: TypedVector[U32], rotation_phase: int):
    rotated_cores = TypedVector[CoreIndex]([])

    for x in c:
        rotated_cores.append(CoreIndex((x + rotation_phase) % CORE_COUNT))

    return rotated_cores

def permute_fn(e: OpaqueHash, t: TimeSlot):
    assignment = TypedVector[U32]([])

    for i in range(VALIDATOR_COUNT):
        assignment.append(U32((CORE_COUNT * i) // VALIDATOR_COUNT))

    shuffled_assignment = shuffle(e, assignment)

    rotation_phase = (t % EPOCH_LENGTH) // ROTATION_PERIOD

    assigned_cores = rotation_fn(shuffled_assignment, rotation_phase)

    return assigned_cores


def assign_fn(state: Sigma):
    assigned_cores = permute_fn(state.eta[2], state.tau)
    vals = state.kappa

    curr_mapping: Dict[CoreIndex, ValidatorList] = {}
    curr_vals: Dict[CoreIndex, TypedVector[ValidatorData]] = {}

    for i, (core, val) in enumerate(zip(assigned_cores, vals)):
        if core not in curr_mapping:
            curr_mapping[core] = ValidatorList([])
            curr_vals[core] = TypedVector[ValidatorData]([])

        curr_mapping[core].append(ValidatorIndex(i))
        curr_vals[core].append(vals[i])

    if state.tau < ROTATION_PERIOD:
        return curr_mapping, curr_vals, curr_mapping, curr_vals

    prev_rot_slot = state.tau - ROTATION_PERIOD
    prev_rot_epoch = prev_rot_slot // EPOCH_LENGTH

    curr_rot_epoch = state.tau // EPOCH_LENGTH

    if prev_rot_epoch == curr_rot_epoch:
        assigned_cores = permute_fn(state.eta[2], prev_rot_slot)
        vals = state.kappa
    else:
        assigned_cores = permute_fn(state.eta[3], prev_rot_slot)
        vals = state.lambda_

    prev_mapping: Dict[CoreIndex, ValidatorList] = {}
    prev_vals: Dict[CoreIndex, TypedVector[ValidatorData]] = {}

    for i, (core, val) in enumerate(zip(assigned_cores, vals)):
        if core not in prev_mapping:
            prev_mapping[core] = ValidatorList([])
            prev_vals[core] = TypedVector[ValidatorData]([])

        prev_mapping[core].append(ValidatorIndex(i))
        prev_vals[core].append(vals[i])

    return curr_mapping, curr_vals, prev_mapping, prev_vals