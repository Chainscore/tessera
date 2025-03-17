from mimetypes import guess_all_extensions

from jam.merklization import MMRFunctions
from jam.state.components.rho import WorkReportState, OptionalWorkReportState
from jam.state.state import State
from jam.types import Block, Null, Bytes
import  dataclasses
from jam.types.protocol.crypto import Hash
from jam.utils.constants import ACCUMULATION_GAS, MAX_DEPENDENCIES, SIGNING_CONTEXTS
from jam.report.error import ReportingError, ReportingErrorCode
from jam.utils.constants import VALIDATOR_COUNT, CORE_COUNT, EPOCH_LENGTH, ROTATION_PERIOD, MAX_WORK_REPORT_SIZE, MIN_VALIDATOR_PER_REPORT
from math import floor
from jam.utils.shuffle import shuffle
from jam.types import  decodable_vector, U32, Vector
from collections import deque
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


@decodable_vector(element_type=U32)
class U32Vector(Vector): ...

class Reporting:

    @staticmethod
    def transition(pre_state:State, block:Block)->State:
        new_state:State = dataclasses.replace(pre_state)

        Reporting.refinement_fn(pre_state, block)
        Reporting.bad_core_index(pre_state, block)
        Reporting.result_fn(pre_state,block)
        Reporting.duplicate_pkg_recent_history(pre_state,block)
        Reporting.duplicate_pkg_report( block)
        Reporting.verify_guarantees_order(block)
        Reporting.big_work_report_output(pre_state, block)
        Reporting.wrong_assignment(pre_state, block)

        for x in block.extrinsic.guarantees:
            pre_state.rho[x.report.core_index] = OptionalWorkReportState(
                WorkReportState(
                    report=block.extrinsic.guarantees[x.report.core_index].report,
                    timeout=block.header.slot
                )
            )

        return new_state

    @staticmethod
    def bad_core_index(state: State, block: Block):
        guarantee_length = len(block.extrinsic.guarantees)
        for x in block.extrinsic.guarantees:

            #  ------- bad_core_index -----------------
            if x.report.core_index >= CORE_COUNT:
                raise ReportingError(
                    ReportingErrorCode.BAD_CORE_INDEX,
                    "Core index value is more then CORE_COUNT"
                )

            # -------- core_engaged -------------
            if x.report.core_index < CORE_COUNT:
                if state.rho[x.report.core_index] != Null:
                    raise ReportingError(
                        ReportingErrorCode.CORE_ENGAGED,
                        ""
                    )

            # --------- no_enough_guatantee ------------
            credential_len = len(x.signatures)
            # print('credential length',credential_len)
            if credential_len < MIN_VALIDATOR_PER_REPORT:
                raise ReportingError(
                    ReportingErrorCode.INSUFFICIENT_GUARANTEE,
                    "Work report doesn't have enough validator"
                )

            # -------- bad_validator_index ------------
            for y in x.signatures:
                if y.validator_index >= VALIDATOR_COUNT:
                    raise ReportingError(
                        ReportingErrorCode.BAD_VALIDATOR_INDEX,
                        "validator index(signature) is out of range"
                    )

            # --------- not_sorted_guarantee ---------
            for j in range(len(x.signatures)-1):
                if x.signatures[j].validator_index >= x.signatures[j+1].validator_index:
                    raise ReportingError (
                        ReportingErrorCode.NOT_SORTED_OR_UNIQUE_GUARANTORS,
                        "Signature's validator index order is not sorted"
                    )

            # --------- not-authorized -----------------
            report_auth_hash = x.report.authorizer_hash
            core_index = x.report.core_index
            auth_pool = state.alpha
            if core_index < CORE_COUNT:
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

            # -------- too_many_dependencies ---------
            segment_root = len(x.report.segment_root_lookup)
            prerequisite = len(x.report.context.prerequisites)
            if (segment_root + prerequisite) > MAX_DEPENDENCIES:
                raise ReportingError(
                    ReportingErrorCode.TOO_MANY_DEPENDENCIES,
                    "Work report has many dependencies(segment_lookup + prerequisite) "
                )

            # ---------- future_report_slot -----------------
            if x.slot > block.header.slot:
                raise ReportingError(
                    ReportingErrorCode.FUTURE_REPORT_SLOT
                )

            # -------- report_epoch_before_last ------------
            if x.slot != block.header.slot :
                if block.header.slot - x.slot > 7:
                    raise ReportingError(
                        ReportingErrorCode.REPORT_EPOCH_BEFORE_LAST,
                        "Guarantee work report slot not in recent slots (block history)"
                    )

            # -------- bad_signature ------------
            for y in x.signatures:
                public_key = None
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
    def verify_guarantees_order(block: Block):
        guarantee_length = len(block.extrinsic.guarantees)
        if guarantee_length > 1 :
            for i in range(len(block.extrinsic.guarantees) - 1):
                if block.extrinsic.guarantees[i].report.core_index >= block.extrinsic.guarantees[i + 1].report.core_index:
                    raise ReportingError(
                        ReportingErrorCode.OUT_OF_ORDER_GUARANTEE,
                        "Core index for each guarantee is not in unique"
                    )

    @staticmethod
    def duplicate_pkg_recent_history(state: State,block : Block):
        hashes = []
        for x in block.extrinsic.guarantees:
            hashes.append(x.report.package_spec.hash)

        for i in state.beta:
                # print('in duplicate package')
                # print('packages',hashes[0],i.packages)
                # if i.packages in hashes:
                if any(key in hashes for key in i.packages.keys()):
                    # print('inside recent history')
                    raise ReportingError (
                        ReportingErrorCode.DUPLICATE_PACKAGE,
                        "Work package is already executed in recent-block's history"
                    )

    @staticmethod
    def duplicate_pkg_report( block :Block):
        if len(block.extrinsic.guarantees) > 1:
            for x in range (len(block.extrinsic.guarantees)):
                for y in range(x+1, len(block.extrinsic.guarantees)):
                    if block.extrinsic.guarantees[x].report.package_spec.hash == block.extrinsic.guarantees[y].report.package_spec.hash:
                        raise ReportingError(
                            ReportingErrorCode.DUPLICATE_PACKAGE
                        )

    @staticmethod
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

        mapping =  {keys[i]: values[i] for i in range(len(keys))}

        # array of assign validator for each core
        guarantee_validator_index = {}

        for x in block.extrinsic.guarantees:
            key = x.report.core_index
            value = set()
            for y in x.signatures:
                value.add(y.validator_index)

            guarantee_validator_index[key] =  value

        guarantee_validator_index = {k: guarantee_validator_index[k] for k in (guarantee_validator_index.keys()) }

        for key in guarantee_validator_index:
            if len(guarantee_validator_index[key]) == 3:
                if guarantee_validator_index[key] != mapping.get(key):
                    raise ReportingError (
                        ReportingErrorCode.WRONG_ASSIGNMENT,
                        "Assign wrong validator to the core"
                    )

    @staticmethod
    def refinement_fn(state:State,block:Block):

        exports_root = []
        work_package_hashes = []

        for x in state.beta:
            for key in x.packages:
                work_package_hashes.append(key)
            for key in x.packages:
                exports_root.append(x.packages[key])

        hashes = []
        for report in block.extrinsic.guarantees:
            hashes.append(report.report.package_spec.hash)

        header_hashes = []

        for x in state.beta:
            header_hashes.append(x.header_hash)

        for y in block.extrinsic.guarantees:
            context = y.report.context

            if context.anchor not in header_hashes:
                raise ReportingError(
                    ReportingErrorCode.ANCHOR_NOT_RECENT,
                )

            if not any(item.state_root == context.state_root for item in state.beta):
                raise ReportingError(
                    ReportingErrorCode.BAD_STATE_ROOT
                )

            if context.prerequisites != Null or y.report.segment_root_lookup != Null: # changed from is not None to != Null
                 for x in context.prerequisites:
                    if x not in  hashes and x not in work_package_hashes:
                        raise ReportingError(
                            ReportingErrorCode.DEPENDENCY_MISSING
                        )

            if  y.report.segment_root_lookup != Null:
                # print('segment 2',exports_root)
                for x in y.report.segment_root_lookup:
                    if x.work_package_hash not in hashes and x.work_package_hash not in work_package_hashes or (x.segment_tree_root != y.report.package_spec.exports_root and x.segment_tree_root not in exports_root):
                        raise ReportingError(
                            ReportingErrorCode.SEGMENT_ROOT_LOOKUP_INVALID
                        )

    @staticmethod
    def result_fn(state:State,block:Block):

        results = block.extrinsic.guarantees

        for x in results:
            total_accumulate_gas = 0
            for y in x.report.results:
                if y.service_id not in state.delta:
                    # print("service")
                    raise ReportingError(
                        ReportingErrorCode.BAD_SERVICE_ID
                    )

                if y.code_hash != state.delta[y.service_id].code_hash:
                    raise ReportingError(
                        ReportingErrorCode.BAD_CODE_HASH
                    )

                if y.accumulate_gas < state.delta[y.service_id].min_gas:
                    raise ReportingError(
                        ReportingErrorCode.SERVICE_ITEM_GAS_TOO_LOW
                    )

                total_accumulate_gas = total_accumulate_gas + y.accumulate_gas

            if total_accumulate_gas > ACCUMULATION_GAS:
                raise ReportingError(
                    ReportingErrorCode.WORK_REPORT_GAS_TOO_HIGH
                )

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

    @staticmethod
    def big_work_report_output(state:State, block:Block):
        work_report_output = Bytes(0)

        for x in block.extrinsic.guarantees:
            work_report_output = work_report_output + x.report.auth_output
            for y in x.report.results:
                work_report_output = work_report_output + y.result.get_value()

        if len(work_report_output) > MAX_WORK_REPORT_SIZE:
            raise ReportingError(
                ReportingErrorCode.WORK_REPORT_TOO_BIG
            )



