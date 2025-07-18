# from math import floor
# from collections import deque

# from tsrkit_types import TypedVector, U32
# from tsrkit_types.option import Null

# from jam.state.state import State
# from jam.types import Block, TimeSlot

# from jam.utils.shuffle import shuffle
# from jam.utils.constants import VALIDATOR_COUNT, CORE_COUNT, EPOCH_LENGTH, ROTATION_PERIOD


# def assign_guarantors(slot: TimeSlot = Null, epoch = 0):
#     """
#     Fetch core mappings of guarantors for a specific timeslot or current state's timeslot

#     Args:
#         slot: A Particular Timeslot
#         epoch: 0 for current epoch, -1 for previous epoch and 1 for next epoch

#     Returns:
#         Mapping of core index to its assigned guarantor
#     """

#     # ------ Fetch State --------
#     if slot :
#         from jam.settings import settings

#         ts_key = Block.get_storage_key_slot(slot)
#         hh = settings.main_db.get(ts_key)
#         state = State.load(hh)

#     else:
#         from jam.state.state import state

#     # ------- Validators ---------
#     validators: TypedVector[U32] = TypedVector[U32]([U32(i) for i in range(VALIDATOR_COUNT)])

#     # ------- Unassigned Cores -------
#     validator_assign: TypedVector[U32] = TypedVector[U32]([])
#     for i in range(VALIDATOR_COUNT):
#         val_core = floor((CORE_COUNT * i) / VALIDATOR_COUNT)
#         validator_assign.append(U32(val_core))

#     # ------- Epoch Entropy -------
#     if epoch == 0:
#         epoch_entropy = state.eta[2]
#         validator_set = state.kappa
#     elif epoch == -1:
#         epoch_entropy = state.eta[3]
#         validator_set = state.lambda_
#     elif epoch == 1:
#         epoch_entropy = state.eta[1]
#         validator_set = state.gamma.k
#     else:
#         raise ValueError("Epoch value can be 0, 1 or -1.")

#     # ------- Shuffle Validators -------
#     core_assign = shuffle(epoch_entropy.encode().hex(), validator_assign)

#     # ------- Create Mapping ---------
#     mapping = {}
#     for i in range(VALIDATOR_COUNT):
#         key = core_assign[i]
#         value = validators[i]
#         if key not in mapping:
#             mapping[key] = set()
#         mapping[key].add(value)

#     # ------- Rotate Validators -------
#     # rotation_phase = floor((slot % EPOCH_LENGTH) / ROTATION_PERIOD)
#     keys = list(mapping.keys())
#     values = [mapping[k] for k in keys]
#     values = deque(values)
#     # values.rotate(-rotation_phase)

#     mapping = {keys[i]: (values[i], validator_set[i]) for i in range(VALIDATOR_COUNT)}

#     return mapping
