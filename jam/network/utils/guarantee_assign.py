from jam.utils.constants import VALIDATOR_COUNT, CORE_COUNT, EPOCH_LENGTH, ROTATION_PERIOD
from math import floor
from jam.utils.shuffle import shuffle
from jam.types import  decodable_vector, U32, Vector
from collections import deque


@decodable_vector(element_type=U32)
class U32Vector(Vector): ...

def guarantor_assignment(eta,  kappa, lambda_, block_slot, report_slot):

    """
    Description:
        In this given function take some entropy according to epoch and slot and create mapping between core and validator.

    Args :
        eta: define as entropy
        kappa:  help to get current validator data
        lambda_: help to get the previous validator data
        block_slot: through this we get the current block's slot
        report_slot: slot assigned to the work report

    Return:
        It's return the dict that is mapping between core and validator
    """
    # ------- validator order ---------
    array_validator: U32Vector = U32Vector([])
    for i in range(VALIDATOR_COUNT):
        array_validator.append(U32(i))

    # ------- validator assignment to the cores -------
    validator_assign: U32Vector = U32Vector([])
    for i in range(VALIDATOR_COUNT):
        val_core = floor((CORE_COUNT * i) / VALIDATOR_COUNT)
        validator_assign.append(U32(val_core))

    # <------------- Entropy for current epoch ------------------>
    epoch_entropy = eta[2]



    # ------- shuffle validator with respect to the given entropy -------
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
    rotation_phase = floor((work_report_slot % EPOCH_LENGTH) / ROTATION_PERIOD)
    keys = list(mapping.keys())
    values = [mapping[k] for k in keys]
    values = deque(values)
    values.rotate(-rotation_phase)

    mapping = {keys[i]: values[i] for i in range(len(keys))}

    return mapping
