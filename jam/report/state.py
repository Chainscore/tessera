from jam.state.components.rho import WorkReportState, OptionalWorkReportState
from jam.state.state import State
from jam.types import Block, Null, Bytes
import  dataclasses
from jam.types.protocol.crypto import Hash
from jam.utils.constants import ACCUMULATION_GAS, MAX_DEPENDENCIES, SIGNING_CONTEXTS
from jam.report.error import ReportingError, ReportingErrorCode
from jam.utils.constants import VALIDATOR_COUNT, CORE_COUNT, EPOCH_LENGTH, ROTATION_PERIOD, MAX_WORK_REPORT_SIZE, MIN_VALIDATOR_PER_REPORT
from math import floor
from jam.types import  decodable_vector, U32, Vector
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from jam.report.guarantee_assignment import wrong_assignment


@decodable_vector(element_type=U32)
class U32Vector(Vector): ...

class Reporting:

    @staticmethod
    def transition(state:State, block:Block)->State:
        """
        Description:
            This function takes two arguments: state, block. This transition function check all the boundary cases for work_report and update the state Rho.
        Args:
            state: This is the state on which transition happen or another state to get previous and curr data (like validators)
            block: This is the recent block added on-chain and to get all information(like header, slot, extrinsic)

        Returns:
            Returns the updated Rho(workreport, timeslot)
        """
        new_state:State = dataclasses.replace(state)

        for x in block.extrinsic.guarantees:

            #  ------- bad_core_index -----------------
            if x.report.core_index >= CORE_COUNT:
                raise ReportingError(
                    ReportingErrorCode.BAD_CORE_INDEX,
                    "Core index value is more then core range(CORE_COUNT)"
                )

            # -------- core_engaged -------------
            if x.report.core_index < CORE_COUNT:
                if state.rho[x.report.core_index] != Null:
                    raise ReportingError(
                        ReportingErrorCode.CORE_ENGAGED,
                        "The core index mentioned in report should be available in rho"
                    )

            # --------- no_enough_guatantee ------------
            credential_len = len(x.signatures)
            # print('credential length',credential_len)
            if credential_len < MIN_VALIDATOR_PER_REPORT:
                raise ReportingError(
                    ReportingErrorCode.INSUFFICIENT_GUARANTEE,
                    "Work report doesn't has enough validator"
                )

            # -------- bad_validator_index ------------
            for y in x.signatures:
                if y.validator_index >= VALIDATOR_COUNT:
                    raise ReportingError(
                        ReportingErrorCode.BAD_VALIDATOR_INDEX,
                        "Validator index(signature) is out of range"
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
                    "Work report has many dependencies(segment_lookup + prerequisite)"
                )

            # ---------- future_report_slot -----------------
            if x.slot > block.header.slot:
                raise ReportingError(
                    ReportingErrorCode.FUTURE_REPORT_SLOT,
                    "Report's slot should match with header slot"
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
                    Ed25519PublicKey.from_public_bytes(bytes(public_key)).verify(bytes(signature),SIGNING_CONTEXTS['guarantee'] + bytes(Hash.blake2b(x.report.encode())))
                except InvalidSignature:
                    raise ReportingError(
                        ReportingErrorCode.BAD_SIGNATURE,
                        "Signature doesn't match with that particular public key"
                    )

        #------------- out_of_order_guarantee ---------------------
        guarantee_length = len(block.extrinsic.guarantees)
        if guarantee_length > 1:
            for i in range(len(block.extrinsic.guarantees) - 1):
                if block.extrinsic.guarantees[i].report.core_index >= block.extrinsic.guarantees[
                    i + 1].report.core_index:
                    raise ReportingError(
                        ReportingErrorCode.OUT_OF_ORDER_GUARANTEE,
                        "Core index for each guarantee is not in unique"
                    )

        # --------------- duplicated_package_in_recent_history ----------------------------
        hashes = []
        for x in block.extrinsic.guarantees:
            hashes.append(x.report.package_spec.hash)

        for i in state.beta:
            if any(key in hashes for key in i.packages.keys()):
                raise ReportingError(
                    ReportingErrorCode.DUPLICATE_PACKAGE,
                    "Work package is already executed in recent-block's history"
                )

        #--------------------------duplicated_package_in_reports----------------------------
        if len(block.extrinsic.guarantees) > 1:
            for x in range (len(block.extrinsic.guarantees)):
                for y in range(x+1, len(block.extrinsic.guarantees)):
                    if block.extrinsic.guarantees[x].report.package_spec.hash == block.extrinsic.guarantees[y].report.package_spec.hash:
                        raise ReportingError(
                            ReportingErrorCode.DUPLICATE_PACKAGE,
                            "Duplicate package spec hash in other report of same guarantee"
                        )

        # --------------- too_big_work_report -------------------
        work_report_output = Bytes(0)

        for x in block.extrinsic.guarantees:
            work_report_output = work_report_output + x.report.auth_output
            for y in x.report.results:
                work_report_output = work_report_output + y.result.get_value()

        if len(work_report_output) > MAX_WORK_REPORT_SIZE:
            raise ReportingError(
                ReportingErrorCode.WORK_REPORT_TOO_BIG,
                "Length of sum of result and auth_output should be less than 48 * 2**10 "
            )

        Reporting.refinement_fn(state, block)
        Reporting.result_fn(state,block)
        wrong_assignment(state, block)

        for x in block.extrinsic.guarantees:
            state.rho[x.report.core_index] = OptionalWorkReportState(
                WorkReportState(
                    report=block.extrinsic.guarantees[x.report.core_index].report,
                    timeout=block.header.slot
                )
            )

        return new_state


    @staticmethod
    def refinement_fn(state:State,block:Block):

        exports_root = []
        work_package_hashes = []

        for x in state.beta:
            for key in x.packages:
                work_package_hashes.append(key)
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
                    "Anchor hash should match with header hash of any block in recent history"
                )

            if not any(item.state_root == context.state_root for item in state.beta):
                raise ReportingError(
                    ReportingErrorCode.BAD_STATE_ROOT,
                    "State_root should match with any block state_root in recent history"
                )

            if context.prerequisites != Null or y.report.segment_root_lookup != Null: # changed from is not None to != Null
                 for x in context.prerequisites:
                    if x not in hashes and x not in work_package_hashes:
                        raise ReportingError(
                            ReportingErrorCode.DEPENDENCY_MISSING,
                            ""
                        )

            if  y.report.segment_root_lookup != Null:
                for x in y.report.segment_root_lookup:
                    if x.work_package_hash not in hashes and x.work_package_hash not in work_package_hashes or (x.segment_tree_root != y.report.package_spec.exports_root and x.segment_tree_root not in exports_root):
                        raise ReportingError(
                            ReportingErrorCode.SEGMENT_ROOT_LOOKUP_INVALID,
                            "Work-packages mentioned in the segment-root lookup, be either in the extrinsic or in our recent history."
                        )

    @staticmethod
    def result_fn(state:State,block:Block):

        results = block.extrinsic.guarantees

        for x in results:
            total_accumulate_gas = 0
            for y in x.report.results:
                if y.service_id not in state.delta:
                    raise ReportingError(
                        ReportingErrorCode.BAD_SERVICE_ID,
                        "Service_id of each report should match with id of delta"
                    )

                if y.code_hash != state.delta[y.service_id].code_hash:
                    raise ReportingError(
                        ReportingErrorCode.BAD_CODE_HASH,
                        "Result code_hash should match with state's delta code_hash"
                    )

                if y.accumulate_gas < state.delta[y.service_id].min_gas:
                    raise ReportingError(
                        ReportingErrorCode.SERVICE_ITEM_GAS_TOO_LOW,
                        "For every report its accumulate gas should be greater than the delta's min_gas"
                    )

                total_accumulate_gas = total_accumulate_gas + y.accumulate_gas

            if total_accumulate_gas > ACCUMULATION_GAS:
                raise ReportingError(
                    ReportingErrorCode.WORK_REPORT_GAS_TOO_HIGH,
                    "Sum of all accumulate gas in result of report should be less than ACCUMULATION_GAS"
                )






