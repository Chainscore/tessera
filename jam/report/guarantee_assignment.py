from jam.state.state import State
from jam.types import Block
from jam.report.error import ReportingError, ReportingErrorCode
from jam.utils.constants import VALIDATOR_COUNT, CORE_COUNT, EPOCH_LENGTH, ROTATION_PERIOD
from math import floor
from jam.utils.shuffle import shuffle
from jam.types import  decodable_vector, U32, Vector
from collections import deque

@decodable_vector(element_type=U32)
class U32Vector(Vector): ...

def wrong_assignment(state: State, block: Block):
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
    epoch_entropy = None
    for x in block.extrinsic.guarantees:
        if x.slot == block.header.slot:
            epoch_entropy = state.eta[2]

    # <------------- Entropy for previous rotation in same epoc ------------------>
    for x in block.extrinsic.guarantees:
        if x.slot != block.header.slot and floor((block.header.slot - ROTATION_PERIOD) / EPOCH_LENGTH) == floor(
                block.header.slot / EPOCH_LENGTH):
            epoch_entropy = state.eta[2]

    # <------------- Entropy for previous rotation but in last epoch ------------------>
    for x in block.extrinsic.guarantees:
        if x.slot != block.header.slot and floor((block.header.slot - ROTATION_PERIOD) / EPOCH_LENGTH) != floor(
                block.header.slot / EPOCH_LENGTH):
            epoch_entropy = state.eta[3]

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
    work_report_slot = None
    for x in block.extrinsic.guarantees:
        work_report_slot = x.slot

    rotation_phase = floor((work_report_slot % EPOCH_LENGTH) / ROTATION_PERIOD)

    keys = list(mapping.keys())

    values = [mapping[k] for k in keys]

    values = deque(values)
    values.rotate(-rotation_phase)

    mapping = {keys[i]: values[i] for i in range(len(keys))}

    # array of assign validator for each core
    guarantee_validator_index = {}

    for x in block.extrinsic.guarantees:
        key = x.report.core_index
        value = set()
        for y in x.signatures:
            value.add(y.validator_index)

        guarantee_validator_index[key] = value

    guarantee_validator_index = {k: guarantee_validator_index[k] for k in (guarantee_validator_index.keys())}

    for key in guarantee_validator_index:
        if len(guarantee_validator_index[key]) == 3:
            if guarantee_validator_index[key] != mapping.get(key):
                raise ReportingError(
                    ReportingErrorCode.WRONG_ASSIGNMENT,
                    "Assign wrong validator to the core"
                )