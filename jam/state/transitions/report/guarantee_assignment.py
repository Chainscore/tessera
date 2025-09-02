from typing import Dict, List

from tsrkit_types.sequences import TypedVector
from tsrkit_types.integers import U32
from jam.types.protocol.core import CoreIndex
from jam.utils.constants import (
    VALIDATOR_COUNT,
    CORE_COUNT,
    EPOCH_LENGTH,
    ROTATION_PERIOD,
)
from math import floor
from jam.utils.shuffle import shuffle
from collections import deque


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
