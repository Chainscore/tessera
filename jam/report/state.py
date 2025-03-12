from xml.dom import NoModificationAllowedErr

from jam.merklization import MMRFunctions
from jam.state.components.rho import WorkReportState, OptionalWorkReportState
from jam.state.state import State
from jam.types import Block, decodable_choice, ServiceId, Boolean, Vector, AvailabilityAssignments, \
    AvailabilityAssignment, Null, String, U64, U16, Bytes
import  dataclasses
from jam.types.extrinsics import GuaranteesExtrinsic
from jam.types.protocol.crypto import Hash
from jam.utils.constants import ACCUMULATION_GAS, MAX_DEPENDENCIES, SIGNING_CONTEXTS
from jam.report.error import ReportingError, ReportingErrorCode
from jam.utils.constants import VALIDATOR_COUNT, CORE_COUNT, EPOCH_LENGTH, ROTATION_PERIOD
from math import floor
from jam.utils.shuffle import shuffle
from jam.types import  decodable_vector, U32, Vector
from jam.types.header import HeaderHash, TimeSlot
from collections import deque
from jam.utils.codec.primitives.integers import encode
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


@decodable_vector(element_type=U32)
class U32Vector(Vector): ...
from jam.types.header import HeaderHash

def generate_report(report : GuaranteesExtrinsic)->GuaranteesExtrinsic:
    guarantees: GuaranteesExtrinsic=Vector(GuaranteesExtrinsic)

    for guarantee in guarantees:
        guarantee.report.package_spec.hash= report[0].report.package_spec.hash
        guarantee.report.package_spec.length = report[0].report.package_spec.length
        guarantee.report.package_spec.erasure_root = report[0].report.package_spec.erasure_root
        guarantee.report.package_spec.exports_root = report[0].report.package_spec.exports_root
        guarantee.report.package_spec.exports_count = report[0].report.package_spec.exports_count

        guarantee.report.context.anchor = report[0].report.context.anchor
        guarantee.report.context.state_root = report[0].report.context.state_root
        guarantee.report.context.beefy_root = report[0].report.context.beefy_root
        guarantee.report.context.lookup_anchor = report[0].report.context.lookup_anchor
        guarantee.report.context.lookup_anchor_slot = report[0].report.context.lookup_anchor_slot
        guarantee.report.context.lookup_anchor_slot = report[0].report.context.lookup_anchor_slot
        guarantee.report.core_index = report[0].report.core_index
        guarantee.report.authorizer_hash = report[0].report.authorizer_hash
        guarantee.report.auth_output = report[0].report.auth_output
        guarantee.report.segment_root_lookup = report[0].report.segment_root_lookup

        for x, y in zip(guarantee.report.results, report[0].report.results):
            x.service_id = y.service_id
            x.code_hash = y.code_hash
            x.payload_hash = y.payload_hash
            x.accumulate_gas = y.accumulate_gas
            x.result = y.resultWorkReport.report.results,report[0].report.results

        guarantee.slot = report[0].slot

        for x, y in zip(guarantee.signatures, report[0].signatures):
            x.validator_index = y.validator_index
            x.signature = y.signature




    return guarantees

class Reporting:

    @staticmethod
    def transition(pre_state:State, block:Block)->State:
        new_state:State = dataclasses.replace(pre_state)


        Reporting.refinement_fn(pre_state, block)
        Reporting.core_engaged(pre_state, block)
        Reporting.bad_core_index(block)
        Reporting.result_fn(pre_state,block)
        Reporting.bad_validator_index(block)
        Reporting.duplicate_pkg_recent_history(pre_state,block)
        Reporting.future_report(block)
        Reporting.no_enough_guarantee(block)
        Reporting.valid_report_fn(pre_state,block)
        Reporting.verify_guarantor_order(block)
        Reporting.duplicate_pkg_report( block)
        Reporting.verify_guarantees_order(block)
        Reporting.check_multiple_dependencies(pre_state,block)
        Reporting.report_last_rotation(block)
        # Reporting.prev_rotation(pre_state, block)
        Reporting.big_work_report_output(pre_state, block)
        Reporting.too_many_dependencies(block)
        Reporting.bad_signature(pre_state, block)
        Reporting.wrong_assignment(pre_state, block)


        return new_state

    @staticmethod
    def bad_core_index(block: Block):
        for x in block.extrinsic.guarantees:
            if x.report.core_index >= CORE_COUNT:
                raise ReportingError(
                    ReportingErrorCode.BAD_CORE_INDEX,
                    "Core index value is more then CORE_COUNT"
                )

    @staticmethod
    def bad_validator_index(block : Block):
        for x in block.extrinsic.guarantees:
            for y in x.signatures:
                if y.validator_index >= VALIDATOR_COUNT:
                    raise ReportingError(
                        ReportingErrorCode.BAD_VALIDATOR_INDEX,
                        "validator index(signature) is out of range"
                    )

    @staticmethod
    def no_enough_guarantee(block:Block):
        for x in block.extrinsic.guarantees:
            credential_len = len(x.signatures)
            print('credential length',credential_len)
            if credential_len < 2:
                raise ReportingError (
                    ReportingErrorCode.INSUFFICIENT_GURANTEE,
                    "Work report don't have enough validator signature"
                )

    @staticmethod
    def too_many_dependencies(block : Block):
        for x in block.extrinsic.guarantees:
            segment_root = len(x.report.segment_root_lookup)
            print("segment_root_lookuo", segment_root)
            prerequisite = len(x.report.context.prerequisites)
            print("prerequisite", prerequisite)
            if (segment_root + prerequisite) > MAX_DEPENDENCIES:
                print((segment_root + prerequisite) > MAX_DEPENDENCIES)
                raise ReportingError (
                    ReportingErrorCode.TOO_MANY_DEPENDENCIES,
                    "Work report has many dependencies(segment_lookup + prerequisite) "
                )

    @staticmethod
    def verify_guarantees_order(block :Block):
        for i in range(len(block.extrinsic.guarantees)-1):
            if block.extrinsic.guarantees[i].report.core_index >= block.extrinsic.guarantees[i+1].report.core_index:
                raise ReportingError (
                    ReportingErrorCode.OUT_OF_ORDER_GUARANTEE,
                    "Core index for each guarantee is not in unique"
                )

    @staticmethod
    def verify_guarantor_order(block: Block):
        for i in block.extrinsic.guarantees:
            for j in range(len(i.signatures)-1):
                if i.signatures[j].validator_index >= i.signatures[j+1].validator_index:
                    raise ReportingError (
                        ReportingErrorCode.NOT_SORTED_OR_UNIQUE_GUARANTORS,
                        "Signature's validator index order is not sorted"
                    )

    @staticmethod
    def valid_report_fn(state: State, block:Block):
        for x in block.extrinsic.guarantees:
            report_auth_hash = x.report.authorizer_hash
            core_index = x.report.core_index
            auth_pool = state.alpha
            print(core_index)
            # print('auth pool length', (state.alpha[core_index]))
            if core_index <2:
                if len(state.alpha[core_index]) == 0:
                    raise ReportingError(
                        ReportingErrorCode.CORE_UNAUTHORIZED,
                        "Pool for that particular core_index in Authorization pool is empty"
                    )
                if report_auth_hash not in auth_pool[core_index]:
                    raise ReportingError(
                        ReportingErrorCode.CORE_UNAUTHORIZED,
                        "Work Report's authorizer_hash not exist in AuthorizationPool"
                    )

    @staticmethod
    def duplicate_pkg_recent_history(state: State,block : Block):
        hashes = []
        for x in block.extrinsic.guarantees:
            hashes.append(x.report.package_spec.hash)

        for i in state.beta:
                print('in duplicate package')
                print('packages',hashes[0],i.packages)
                # if i.packages in hashes:
                if any(key in hashes for key in i.packages.keys()):
                    print('inside recent history')
                    raise ReportingError (
                        ReportingErrorCode.DUPLICATE_PACKAGE,
                        "Work package is already executed in recent-block's history"
                    )

    @staticmethod
    def duplicate_pkg_report( block :Block):
        print('ddduppp')
        if len(block.extrinsic.guarantees)>1:
            for x in range (len(block.extrinsic.guarantees)):
                print('dduuppp1',x,len(block.extrinsic.guarantees))
                for y in range(x+1, len(block.extrinsic.guarantees)): # removed -1 as it was causing error index out of range
                    print('x=',x,'y=',y,'length of gurant',len(block.extrinsic.guarantees))
                    # print('in duplicate package',block.extrinsic.guarantees[x].report.package_spec.hash,block.extrinsic.guarantees[y].report.package_spec.hash)
                    if block.extrinsic.guarantees[x].report.package_spec.hash == block.extrinsic.guarantees[y].report.package_spec.hash:
                        raise ReportingError(
                            ReportingErrorCode.DUPLICATE_PACKAGE
                        )

    @staticmethod
    def report_last_rotation(block :Block):
        for x in block.extrinsic.guarantees:
            if x.slot != block.header.slot :
                if block.header.slot - x.slot > 7:
                    raise ReportingError(
                        ReportingErrorCode.REPORT_EPOCH_BEFORE_LAST,
                        "Guarantee work report slot not in recent slots (block history)"
                    )

    @staticmethod
    def report_rotation(state: State, block: Block):

        # ------- validator order ---------
        array_validator: U32Vector = U32Vector([])
        for i in range(VALIDATOR_COUNT):
            array_validator.append(U32(i))
        print("array_validator =>", array_validator)

        # ------- validator assignment to the cores -------
        validator_assign: U32Vector = U32Vector([])
        for i in range(VALIDATOR_COUNT):
            val_core = floor((CORE_COUNT * i) / VALIDATOR_COUNT)
            validator_assign.append(U32(val_core))
        print("cores_assign => ", validator_assign)

        # <------------- Entropy for current epoch ------------------>
        epoch_entropy = None
        for x in block.extrinsic.guarantees:
            if x.slot == block.header.slot:
                # epoch_entropy = state.eta[2]
                epoch_entropy = "0x7b0aa1735e5ba58d3236316c671fe4f00ed366ee72417c9ed02a53a8019e85b8"

        # <------------- Entropy for previous rotation in same epoc ------------------>
        for x in block.extrinsic.guarantees:
            if x.slot != TimeSlot and floor((block.header.slot - ROTATION_PERIOD)/EPOCH_LENGTH) == floor(block.header.slot / EPOCH_LENGTH):
                # epoch_entropy = state.eta[2]
                epoch_entropy = "0x7b0aa1735e5ba58d3236316c671fe4f00ed366ee72417c9ed02a53a8019e85b8"


        # <------------- Entropy for previous rotation but in last epoch ------------------>
        for x in block.extrinsic.guarantees:
            if x.slot != TimeSlot and floor((block.header.slot - ROTATION_PERIOD)/EPOCH_LENGTH) != floor(block.header.slot / EPOCH_LENGTH):
                # epoch_entropy = state.eta[3]
                epoch_entropy = "0x8c039ff7caa17ccebfcadc44bd9fce6a4b6699c4d03de2e3349aa1dc11193cd7"




        # entropy = "0x7b0aa1735e5ba58d3236316c671fe4f00ed366ee72417c9ed02a53a8019e85b8"
        h = bytes.fromhex(epoch_entropy[2:])
        print("entropy => ", h )

        # ------- shuffle validator with respect to the given entropy -------
        core_assign = shuffle(h, validator_assign)
        print("cores_assign => ", core_assign)

        # Initialize an empty dictionary to store the mapping between core and validator
        mapping = {}

        for i in range(len(array_validator)):
            key = core_assign[i]  # Grouping key from rotated_array
            value = array_validator[i]  # Value from arr_validator

            # If the key is not in the mapping, initialize it as an empty set
            if key not in mapping:
                mapping[key] = set()

            # Add the value (index from arr_validator) to the set for this key
            mapping[key].add(value)

        # Sort the keys of the dictionary (0, 1) and create a new ordered dictionary
        mapping = {k: mapping[k] for k in sorted(mapping.keys())}
        print("assign core to validator", mapping)
        # output => {0:{1, 4, 5}, 1:{0, 2, 3}}
        # mapping[0] = {1, 4, 5}  type set
        # mapping[1] = {0, 2, 3}  type set


        # rotation phase (number of rotation between cores)
        work_report_slot = None
        for x in block.extrinsic.guarantees:
            work_report_slot = x.slot
        print("curr_report_timeslot =>", work_report_slot)
        rotation_phase = floor((work_report_slot % EPOCH_LENGTH) / ROTATION_PERIOD)
        print("rotation_phase => ", rotation_phase)

        keys = list(mapping.keys())  # Get the sorted keys (0, 1)
        print(keys)
        values = [mapping[k] for k in keys]  # Extract the values as a list

        # Use deque for rotation
        values = deque(values)
        values.rotate(-rotation_phase)  # Rotate left (-) or right (+)

        # Reconstruct the mapping
        mapping =  {keys[i]: values[i] for i in range(len(keys))}
        print("mapping after rotaion", mapping)


        # array of assign validator for each core
        guarantee_validator_index = {}

        for x in block.extrinsic.guarantees:
            key = x.report.core_index
            value = set()
            for y in x.signatures:
                value.add(y.validator_index)

            guarantee_validator_index[key] =  value

        guarantee_validator_index = {k: guarantee_validator_index[k] for k in (guarantee_validator_index.keys()) }

        print("guarantee_validator_index => ", guarantee_validator_index)

        guarantor_length = len(block.extrinsic.guarantees)
        print("guarantor_length => ", guarantor_length)


        for key in guarantee_validator_index:
            if guarantee_validator_index[key] == mapping.get(key):
                    # print('core value',core)
                    # print(state.rho.)
                    state.rho[key] = OptionalWorkReportState(
                        WorkReportState(
                            report=block.extrinsic.guarantees[key].report,
                            timeout=block.header.slot
                        )
                    )
            return state




        # add_validator = []

        # Iterate through each group of signatures
        # for group in signatures:
        #     validator_set = set()
        #     for signature in group:
        #         validator_set.add(signature["validator_index"])
        #     add_validator.append(validator_set)
        #
        # print("add_validator =", add_validator)
        # print(add_validator[0])

    @staticmethod
    def prev_rotation(state: State, block: Block):

        # ------- validator order ---------
        array_validator: U32Vector = U32Vector([])
        for i in range(VALIDATOR_COUNT):
            array_validator.append(U32(i))
        print("array_validator =>", array_validator)

        # ------- validator assignment to the cores -------
        validator_assign: U32Vector = U32Vector([])
        for i in range(VALIDATOR_COUNT):
            val_core = floor((CORE_COUNT * i) / VALIDATOR_COUNT)
            validator_assign.append(U32(val_core))
        print("cores_assign => ", validator_assign)

        # <------------- Entropy for current epoch ------------------>
        epoch_entropy = None
        # for x in block.extrinsic.guarantees:
        #     if x.slot == block.header.slot:
        #         # epoch_entropy = state.eta[2]
        #         epoch_entropy = "0x7b0aa1735e5ba58d3236316c671fe4f00ed366ee72417c9ed02a53a8019e85b8"

        # <------------- Entropy for previous rotation in same epoc ------------------>
        # for x in block.extrinsic.guarantees:
        #     if x.slot != TimeSlot and floor((block.header.slot - ROTATION_PERIOD)/EPOCH_LENGTH) == floor(block.header.slot / EPOCH_LENGTH):
        #         # epoch_entropy = state.eta[2]
        #         epoch_entropy = "0x7b0aa1735e5ba58d3236316c671fe4f00ed366ee72417c9ed02a53a8019e85b8"


        # <------------- Entropy for previous rotation but in last epoch ------------------>
        for x in block.extrinsic.guarantees:
            if x.slot != block.header.slot and floor((block.header.slot - ROTATION_PERIOD)/EPOCH_LENGTH) != floor(block.header.slot / EPOCH_LENGTH):
                epoch_entropy = state.eta[3]
                # epoch_entropy = "0x8c039ff7caa17ccebfcadc44bd9fce6a4b6699c4d03de2e3349aa1dc11193cd7"

        # entropy = "0x7b0aa1735e5ba58d3236316c671fe4f00ed366ee72417c9ed02a53a8019e85b8"
        h = bytes.fromhex(epoch_entropy[2:])
        # print("entropy => ", h )

        # ------- shuffle validator with respect to the given entropy -------
        core_assign = shuffle(h, validator_assign)
        print("cores_assign => ", core_assign)

        # Initialize an empty dictionary to store the mapping between core and validator
        mapping = {}

        for i in range(len(array_validator)):
            key = core_assign[i]  # Grouping key from rotated_array
            value = array_validator[i]  # Value from arr_validator

            # If the key is not in the mapping, initialize it as an empty set
            if key not in mapping:
                mapping[key] = set()

            # Add the value (index from arr_validator) to the set for this key
            mapping[key].add(value)

        # Sort the keys of the dictionary (0, 1) and create a new ordered dictionary
        mapping = {k: mapping[k] for k in sorted(mapping.keys())}
        print("assign core to validator", mapping)
        # output => {0:{1, 4, 5}, 1:{0, 2, 3}}
        # mapping[0] = {1, 4, 5}  type set
        # mapping[1] = {0, 2, 3}  type set


        # rotation phase (number of rotation between cores)
        work_report_slot = None
        for x in block.extrinsic.guarantees:
            work_report_slot = x.slot
        print("curr_report_timeslot =>", work_report_slot)
        rotation_phase = floor((work_report_slot % EPOCH_LENGTH) / ROTATION_PERIOD)
        print("rotation_phase => ", rotation_phase)

        keys = list(mapping.keys())  # Get the sorted keys (0, 1)
        print(keys)
        values = [mapping[k] for k in keys]  # Extract the values as a list

        # Use deque for rotation
        values = deque(values)
        values.rotate(-rotation_phase)  # Rotate left (-) or right (+)

        # Reconstruct the mapping
        mapping =  {keys[i]: values[i] for i in range(len(keys))}
        print("mapping after rotaion", mapping)


        # array of assign validator for each core
        guarantee_validator_index = {}

        for x in block.extrinsic.guarantees:
            key = x.report.core_index
            value = set()
            for y in x.signatures:
                value.add(y.validator_index)

            guarantee_validator_index[key] =  value

        guarantee_validator_index = {k: guarantee_validator_index[k] for k in (guarantee_validator_index.keys()) }

        print("guarantee_validator_index => ", guarantee_validator_index)

        guarantor_length = len(block.extrinsic.guarantees)
        print("guarantor_length => ", guarantor_length)

        for key in guarantee_validator_index:
            print("hjhjvgvdhgvvdhgdhgdhhvhvdhv", guarantee_validator_index[key] == mapping.get(key))
            if guarantee_validator_index[key] == mapping.get(key):
                print("hhheeeelooooo")
                # print(state.rho.)
                print(block.extrinsic.guarantees[key].slot,key)
                state.rho[key] = OptionalWorkReportState(
                    WorkReportState(
                        report=block.extrinsic.guarantees[key].report,
                        timeout=block.header.slot
                    )
                )
                return state

    @staticmethod
    def wrong_assignment(state: State, block: Block):

        # ------- validator order ---------
        array_validator: U32Vector = U32Vector([])
        for i in range(VALIDATOR_COUNT):
            array_validator.append(U32(i))
        print("array_validator =>", array_validator)

        # ------- validator assignment to the cores -------
        validator_assign: U32Vector = U32Vector([])
        for i in range(VALIDATOR_COUNT):
            val_core = floor((CORE_COUNT * i) / VALIDATOR_COUNT)
            validator_assign.append(U32(val_core))
        print("cores_assign => ", validator_assign)

        # <------------- Entropy for current epoch ------------------>
        epoch_entropy = None
        for x in block.extrinsic.guarantees:
            if x.slot == block.header.slot:
                # epoch_entropy = state.eta[2]
                epoch_entropy = "0x7b0aa1735e5ba58d3236316c671fe4f00ed366ee72417c9ed02a53a8019e85b8"

        # # <------------- Entropy for previous rotation in same epoc ------------------>
        # for x in block.extrinsic.guarantees:
        #     if x.slot != TimeSlot and floor((block.header.slot - ROTATION_PERIOD)/EPOCH_LENGTH) == floor(block.header.slot / EPOCH_LENGTH):
        #         # epoch_entropy = state.eta[2]
        #         epoch_entropy = "0x7b0aa1735e5ba58d3236316c671fe4f00ed366ee72417c9ed02a53a8019e85b8"
        #
        #
        # # <------------- Entropy for previous rotation but in last epoch ------------------>
        # for x in block.extrinsic.guarantees:
        #     if x.slot != TimeSlot and floor((block.header.slot - ROTATION_PERIOD)/EPOCH_LENGTH) != floor(block.header.slot / EPOCH_LENGTH):
        #         # epoch_entropy = state.eta[3]
        #         epoch_entropy = "0x8c039ff7caa17ccebfcadc44bd9fce6a4b6699c4d03de2e3349aa1dc11193cd7"




        # entropy = "0x7b0aa1735e5ba58d3236316c671fe4f00ed366ee72417c9ed02a53a8019e85b8"
        h = bytes.fromhex(epoch_entropy[2:])
        print("entropy => ", h )

        # ------- shuffle validator with respect to the given entropy -------
        core_assign = shuffle(h, validator_assign)
        print("cores_assign => ", core_assign)

        # Initialize an empty dictionary to store the mapping between core and validator
        mapping = {}

        for i in range(len(array_validator)):
            key = core_assign[i]  # Grouping key from rotated_array
            value = array_validator[i]  # Value from arr_validator

            # If the key is not in the mapping, initialize it as an empty set
            if key not in mapping:
                mapping[key] = set()

            # Add the value (index from arr_validator) to the set for this key
            mapping[key].add(value)

        # Sort the keys of the dictionary (0, 1) and create a new ordered dictionary
        mapping = {k: mapping[k] for k in sorted(mapping.keys())}
        print("assign core to validator", mapping)
        # output => {0:{1, 4, 5}, 1:{0, 2, 3}}
        # mapping[0] = {1, 4, 5}  type set
        # mapping[1] = {0, 2, 3}  type set


        # rotation phase (number of rotation between cores)
        work_report_slot = None
        for x in block.extrinsic.guarantees:
            work_report_slot = x.slot
        print("curr_report_timeslot =>", work_report_slot)
        rotation_phase = floor((work_report_slot % EPOCH_LENGTH) / ROTATION_PERIOD)
        print("rotation_phase => ", rotation_phase)

        keys = list(mapping.keys())  # Get the sorted keys (0, 1)
        print(keys)
        values = [mapping[k] for k in keys]  # Extract the values as a list

        # Use deque for rotation
        values = deque(values)
        values.rotate(-rotation_phase)  # Rotate left (-) or right (+)

        # Reconstruct the mapping
        mapping =  {keys[i]: values[i] for i in range(len(keys))}
        print("mapping after rotaion", mapping)

        # array of assign validator for each core
        guarantee_validator_index = {}

        for x in block.extrinsic.guarantees:
            key = x.report.core_index
            value = set()
            for y in x.signatures:
                value.add(y.validator_index)

            guarantee_validator_index[key] =  value

        guarantee_validator_index = {k: guarantee_validator_index[k] for k in (guarantee_validator_index.keys()) }

        print("guarantee_validator_index => ", guarantee_validator_index)

        guarantor_length = len(block.extrinsic.guarantees)
        print("guarantor_length => ", guarantor_length)

        for key in guarantee_validator_index:
            print(len(guarantee_validator_index[key]))
            if len(guarantee_validator_index[key]) == 3:
                if guarantee_validator_index[key] != mapping.get(key):
                    print("----------------------------------------------------------------------")
                    raise ReportingError (
                        ReportingErrorCode.WRONG_ASSIGNMENT,
                        "Assign wrong validator to the core"
                    )

    @staticmethod
    def bad_signature(state: State, block: Block):
        for x in block.extrinsic.guarantees:
            for y in x.signatures:
                public_key = None
                # take curr
                if x.slot == block.header.slot or x.slot != block.header.slot and floor((block.header.slot - ROTATION_PERIOD)/EPOCH_LENGTH) == floor(block.header.slot / EPOCH_LENGTH):
                    public_key = state.kappa[y.validator_index].ed25519
                elif x.slot != block.header.slot and floor((block.header.slot - ROTATION_PERIOD) / EPOCH_LENGTH) != floor(block.header.slot / EPOCH_LENGTH):
                    public_key = state.lambda_[y.validator_index].ed25519
                signature = y.signature
                try:
                    # print(Ed25519PublicKey.from_public_bytes(bytes(public_key)).verify(bytes(signature),SIGNING_CONTEXTS['guarantee'] + bytes(Hash.blake2b(x.report.encode()))))
                    Ed25519PublicKey.from_public_bytes(bytes(public_key)).verify(bytes(signature),SIGNING_CONTEXTS['guarantee'] + bytes(Hash.blake2b(x.report.encode())))
                except InvalidSignature:
                    raise ReportingError(
                        ReportingErrorCode.BAD_SIGNATURE,
                        "signature doesn't match with the public key"
                    )

    @staticmethod
    def refinement_fn(state:State,block:Block):

        exports_root = []




        work_package_hashes = []

        for x in state.beta:
            for key in x.packages:
                work_package_hashes.append(key)
            for key in x.packages:

                # print('segment root',x.packages.values())
                exports_root.append(x.packages[key])

        hashes = []
        #
        for report in block.extrinsic.guarantees:
        #     report.
            hashes.append(report.report.package_spec.hash)

        header_hashes = []

        for x in state.beta:
            header_hashes.append(x.header_hash)

        print(header_hashes)
        for y in block.extrinsic.guarantees:
            context = y.report.context

            if context.anchor not in header_hashes:
                print(context.anchor)
                raise ReportingError(
                    ReportingErrorCode.ANCHOR_NOT_RECENT
                )


            if not any(item.state_root == context.state_root for item in state.beta):
                raise ReportingError(
                    ReportingErrorCode.BAD_STATE_ROOT
                )

            # else:
            #     raise ReportingError(
            #         ReportingErrorCode.BAD_BEEFY_MMR_ROOT
            #     )

            # if context.lookup_anchor not in state.beta[:context.lookup_anchor_slot]:
            #     return 'err'



            # In this we are checking if prerequisites array is not null , then
            # its hashes must match with package spec hash of previous reports
            if context.prerequisites != Null or y.report.segment_root_lookup != Null: # changed from is not None to != Null
                # print(context.prerequisites != Null)
                 for x in context.prerequisites:
                    print('x = ',x,'work package',work_package_hashes,'hashes ',hashes)
                    if x not in  hashes and x not in work_package_hashes:
                        raise ReportingError(
                            ReportingErrorCode.DEPENDENCY_MISSING
                        )
            print('segment')
            # segment_root_lookup_invalid-1.json
            if  y.report.segment_root_lookup != Null:
                # print('segment 2',exports_root)
                for x in y.report.segment_root_lookup:
                    # print(x.segment_tree_root != y.report.package_spec.exports_root)
                    # print(x.work_package_hash not in hashes and x.work_package_hash not in work_package_hashes and (x.segment_tree_root != y.report.package_spec.exports_root and x.segment_tree_root != exports_root))
                    if x.work_package_hash not in hashes and x.work_package_hash not in work_package_hashes or (x.segment_tree_root != y.report.package_spec.exports_root and x.segment_tree_root not in exports_root):
                        raise ReportingError(
                            ReportingErrorCode.SEGMENT_ROOT_LOOKUP_INVALID
                        )

    @staticmethod
    def result_fn(state:State,block:Block):

        results = block.extrinsic.guarantees
        # print(SIGNING_CONTEXTS['beefy'])
        a = (Hash.keccak256(bytes(state.beta[6].mmr[0].get_value())+ bytes(state.beta[6].mmr[1].get_value())))
        b = Hash.keccak256(bytes(state.beta[6].mmr[2].get_value())+bytes(state.beta[6].mmr[3].get_value()))
        # print(a,b)
        # print(Hash.keccak256(Bytes(4c31a1024d553c6f5eb90a26f9c53507d6d58b7be1197c0f86054b084353de5f7f64e54f8be039cea06582eb38e7f36f924c1f59a0f3043b4df6f140cccd6ddfd7cc7a7751048dbe8d0232b5d0273acd874e56c19e41a2e09b590ca00e59908d)))
        a = bytes("jam_beefy", 'utf-8')
        MMRFunc = MMRFunctions()
        # print("mmr value", state.beta[-1].mmr)
        # print('encode', state.beta[-1].mmr.encode().hex())

        # print("peak value", MMRFunc.super_peak(state.beta[-1].mmr))


        # print('peak value',MMRFunc.super_peak(state.beta[6].mmr), block.extrinsic.guarantees[0].report.context.beefy_root)
        # print('signature value',(a + bytes(Hash.keccak256(state.beta[6].mmr.encode()))).hex())
        # print('hashhhe',Hash.keccak256(bytes((state.beta[6].mmr[0]).get_value()) + bytes(state.beta[6].mmr[2].get_value()) + bytes(state.beta[6].mmr[3].get_value()) + bytes(state.beta[6].mmr[1].get_value())))
        # print('mmmmrrr',Hash.keccak256((MMRFunctions.encode_mmr(state.beta[6].mmr))))

        for x in results:
            total_accumulate_gas = 0
            for y in x.report.results:
                if y.service_id not in state.delta:
                    print("service")
                    raise ReportingError(
                        ReportingErrorCode.BAD_SERVICE_ID
                    )
                print('in code hash')
                if y.code_hash != state.delta[y.service_id].code_hash:
                    raise ReportingError(
                        ReportingErrorCode.BAD_CODE_HASH
                    )
                print('outside service id')

                if y.accumulate_gas < state.delta[y.service_id].min_gas:
                    raise ReportingError(
                        ReportingErrorCode.SERVICE_ITEM_GAS_TOO_LOW
                    )

                total_accumulate_gas = total_accumulate_gas + y.accumulate_gas


            print('high gas',total_accumulate_gas , ACCUMULATION_GAS )
            if total_accumulate_gas > ACCUMULATION_GAS:
                # print(state.beta)
                # print(Hash.keccak256(bytes(0xf5df0c11416d43c55b43e096572d450b7780ed0fd7b540f26c8ded8e0d41e183)))
                raise ReportingError(
                    ReportingErrorCode.WORK_REPORT_GAS_TOO_HIGH
                )
            if total_accumulate_gas <= ACCUMULATION_GAS:
                # print('in high work report gas',total_accumulate_gas)
                print('high work report gas case')
                for core in range(len(block.extrinsic.guarantees)):
                    # print('core value',core)
                        # print(state.rho.)
                    state.rho[core] = OptionalWorkReportState(
                        WorkReportState(
                            report=block.extrinsic.guarantees[core].report,
                            timeout=block.header.slot
                            )
                        )
                    # print(core,'---> ',state.rho[core])
                    # print(core,'--->',block.extrinsic.guarantees[core].report)
                return state

        # for x in transition().rho:
        #     for y in x.report.results:
        #         if not y.accumulate_gas >= transition().delta[ServiceId].min_gas:
        #             return 'err'
        #         total_accumulate_gas = sum + y.accumulate_gas
        #     if not sum <= ACCUMULATION_GAS:
        #         return 'err'

        #
        # for x in results:
        #
        #     # checking if code hash in results is available in state code hash or not
        #     if x.code_hash != state.delta[0].code_hash:
        #         return 'err'


        #
        #     if x.accumulate_gas <= state.delta[0].min_gas:
        #         return 'err'
        #
        #     total_accumulate_gas = total_accumulate_gas + x.accumulate_gas
        #
        # if total_accumulate_gas >= ACCUMULATION_GAS:
        #     return 'err'
        #
        # state.beta[0]

    @staticmethod
    def workreport_package( block:Block ) :
        hashes = []

        # storing package_spec hash of all reports in hashes
        for x in block.extrinsic.guarantees:
            if x.report.package_spec.hash not in hashes:
                hashes.append(x.report.package_spec.hash)
            else :
                raise ReportingError(
                    ReportingErrorCode.DUPLICATE_PACKAGE_IN_REPORT,
                    "Two work reports of the same package(no duplicate work-package hash)"
                )

        # @staticmethod
        # def ensure_assurances_unique(assurances: List[AvailAssurance]) -> None:
        #     """Ensure the assurances are unique using Python's set"""
        #     if len(assurances) != len(set(assurance.validator_index for assurance in assurances)):
        #         raise AssurancesError(AssurancesErrorCode.NOT_SORTED_OR_UNIQUE_ASSURERS,
        #                               "Assurances are not unique by validator index")



        for x in block.extrinsic.guarantees:
            if x.report.package_spec.hash in hashes:
                return 'err'

    @staticmethod
    def core_engaged(state:State,block:Block):
        for x in block.extrinsic.guarantees:
            print('xxxxxcore')
            # print(x.report.core_index,state.rho[x.report.core_index])
            if x.report.core_index <= 2:
                if state.rho[x.report.core_index] != Null:
                    raise ReportingError(
                        ReportingErrorCode.CORE_ENGAGED
                    )

    @staticmethod
    def future_report(block:Block):
        for x in block.extrinsic.guarantees:
            if x.slot > block.header.slot:
                raise ReportingError(
                    ReportingErrorCode.FUTURE_REPORT_SLOT
                )

    @staticmethod
    # def check_multiple_reports(state:State, block:Block):
    #     if len(block.extrinsic.guarantees) >1:
    #         for core in range(len(block.extrinsic.guarantees)):
    #             # print('core value',core)
    #                 # print(state.rho.)
    #             state.rho[core] = OptionalWorkReportState(
    #                 WorkReportState(
    #                     report=block.extrinsic.guarantees[core].report,
    #                     timeout=block.extrinsic.guarantees[core].slot
    #                     )
    #                 )
    #         return state

    @staticmethod
    def check_multiple_dependencies(state:State, block:Block):
        for x in block.extrinsic.guarantees:
            if len(x.report.context.prerequisites)> 0 and len(x.report.segment_root_lookup)>0:
                for core in range(len(block.extrinsic.guarantees)):
                        # print('core value',core)
                        # print(state.rho.)
                    state.rho[core] = OptionalWorkReportState(
                            WorkReportState(
                                report=block.extrinsic.guarantees[core].report,
                                timeout=block.header.slot
                            )
                        )
        return state

    @staticmethod
    def big_work_report_output(state:State, block:Block):
        work_report_output = Bytes(0)

        for x in block.extrinsic.guarantees:

            work_report_output = work_report_output + x.report.auth_output

            for y in x.report.results:
                work_report_output = work_report_output + y.result.get_value()
        # print(work_report_output < Bytes(48 * (2 ** 10)))
        print(len(work_report_output),48*(2**10))
        if len(work_report_output) > (48 * (2**10)):
            raise ReportingError(
                ReportingErrorCode.WORK_REPORT_TOO_BIG
            )
        if len(work_report_output) <= (48 * (2 ** 10)):
            for core in range(len(block.extrinsic.guarantees)):
                # print('core value',core)
                # print(state.rho.)
                state.rho[core] = OptionalWorkReportState(
                    WorkReportState(
                        report=block.extrinsic.guarantees[core].report,
                        timeout=block.header.slot
                    )
                )
        return state
        # print('total output',work_report_output)



