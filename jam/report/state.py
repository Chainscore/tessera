from typing import Dict, Set, List

from jam.merklization import MMRFunctions
from jam.types.base import decodable_vector, U32, Vector, Bytes, Null, Int
from jam.types.protocol.core import CoreIndex
from jam.types.state.pi import AllCoreStats, ServiceStat, AllServiceStats
from jam.types.state.rho import WorkReportState, OptionalWorkReportState
from jam.types.state.sigma import Sigma
from jam.types.block import Block
import  dataclasses
from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.types.work.report import WorkReport
from jam.utils.constants import ACCUMULATION_GAS, MAX_DEPENDENCIES, SIGNING_CONTEXTS, LOOKUP_ANCHOR_MAX_AGE
from jam.report.error import ReportingError, ReportingErrorCode
from jam.utils.constants import VALIDATOR_COUNT, CORE_COUNT, EPOCH_LENGTH, ROTATION_PERIOD, MAX_WORK_REPORT_SIZE
from math import floor
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from jam.report.guarantee_assignment import guarantor_assignment


@decodable_vector(element_type=U32)
class U32Vector(Vector): ...

class Reporting:

    @staticmethod
    def transition(state: Sigma, block:Block, known_packages: List[OpaqueHash]) -> Sigma:
        """
        Description:
            This function takes two arguments: state, block. This transition function check all the boundary cases for work_report and update the state Rho.
        Args:
            state: This is the state on which transition happen or another state to get previous and curr data (like validators)
            block: This is the recent block added on-chain and to get all information(like header, slot, extrinsic)
            known_packages: Packages from known queue (Nu), accumulation history (Xi)

        Returns:
            Returns the updated Rho(workreport, timeslot)
        """

        # small w
        all_reports = []
        wp_hash_set = set()

        for guarantee in block.extrinsic.guarantees:
            report = guarantee.report
            # -------- too_many_dependencies ---------
            # https://graypaper.fluffylabs.dev/#/85129da/13ab0013b600?v=0.6.3
            segment_root = len(report.segment_root_lookup)
            prerequisite = len(report.context.prerequisites)
            if (segment_root + prerequisite) > MAX_DEPENDENCIES:
                raise ReportingError(
                    ReportingErrorCode.TOO_MANY_DEPENDENCIES,
                    "Work report has many dependencies(segment_lookup + prerequisite)"
                )

            Reporting.verify_report_output(report)

            #  ------- bad_core_index -----------------
            if report.core_index >= CORE_COUNT:
                raise ReportingError(
                    ReportingErrorCode.BAD_CORE_INDEX,
                    "Core index value is more then core range(CORE_COUNT)"
                )

            # -------- core_engaged -------------
            # Ensure Rho is empty for this report
            # 11.29
            if state.rho[report.core_index] != Null:
                raise ReportingError(
                    ReportingErrorCode.CORE_ENGAGED,
                    "The core index mentioned in report should be available in rho"
                )

            # --------- no_enough_guatantee ------------
            # https://graypaper.fluffylabs.dev/#/85129da/147002149002?v=0.6.3
            credential_len = len(guarantee.signatures)
            if credential_len < 2:
                raise ReportingError(
                    ReportingErrorCode.INSUFFICIENT_GUARANTEE,
                    "Work report doesn't has enough validator"
                )

            # -------- bad_validator_index ------------
            for y in guarantee.signatures:
                if y.validator_index >= VALIDATOR_COUNT:
                    raise ReportingError(
                        ReportingErrorCode.BAD_VALIDATOR_INDEX,
                        "Validator index(signature) is out of range"
                    )

            # --------- not_sorted_guarantee ---------
            # 11.25
            # https://graypaper.fluffylabs.dev/#/85129da/14b80214df02?v=0.6.3
            for j in range(len(guarantee.signatures)-1):
                if guarantee.signatures[j].validator_index >= guarantee.signatures[j+1].validator_index:
                    raise ReportingError (
                        ReportingErrorCode.NOT_SORTED_OR_UNIQUE_GUARANTORS,
                        "Signature's validator index order is not sorted"
                    )

            # --------- not-authorized -----------------
            # https://graypaper.fluffylabs.dev/#/85129da/15ea0015f700?v=0.6.3
            # Ensure authorizer hash is present in core's Authorizer Pool
            if report.authorizer_hash not in state.alpha[int(report.core_index)]:
                raise ReportingError(
                    ReportingErrorCode.CORE_UNAUTHORIZED,
                    "Work Report's authorizer_hash not exist in AuthorizationPool"
                )


            # ---------- future_report_slot -----------------
            if guarantee.slot > block.header.slot:
                raise ReportingError(
                    ReportingErrorCode.FUTURE_REPORT_SLOT,
                    "Report's slot more then block's slot"
                )

            # -------- report_epoch_before_last ------------
            if guarantee.slot != block.header.slot :
                if block.header.slot - guarantee.slot > 7:
                    raise ReportingError(
                        ReportingErrorCode.REPORT_EPOCH_BEFORE_LAST,
                        "Guarantee work report slot not in recent slots (block history)"
                    )

            # --------------- duplicated_package_in_recent_history ----------------------------
            # https://graypaper.fluffylabs.dev/#/85129da/157a0115c901?v=0.6.3
            wp_hash_set.add(report.package_spec.hash)
            all_reports.append(report)

        #------------- out_of_order_guarantee ---------------------
        # 11.23
        # https://graypaper.fluffylabs.dev/#/85129da/146802146902?v=0.6.3
        guarantee_length = len(block.extrinsic.guarantees)
        if guarantee_length > 1:
            for i in range(len(block.extrinsic.guarantees) - 1):
                if block.extrinsic.guarantees[i].report.core_index >= block.extrinsic.guarantees[
                    i + 1].report.core_index:
                    raise ReportingError(
                        ReportingErrorCode.OUT_OF_ORDER_GUARANTEE,
                        "Core index for each guarantee is not in unique"
                    )


        recent_exports_roots = {}
        beta_wp_hashes = []

        for x in state.beta:
            for key in x.packages:
                beta_wp_hashes.append(key)
                recent_exports_roots.update(x.packages)

        recent_exports_roots.update({report.package_spec.hash: report.package_spec.exports_root for report in all_reports})

        rho_package_hashes = [pending_wr.get_value().report.package_spec.hash if pending_wr.is_some() else None for pending_wr in state.rho]
        for p in wp_hash_set:
            # Ensure this WP is not previously executed - checking Beta, Nu, Rho, Xi
            # 11.38
            if p in beta_wp_hashes or p in known_packages or p in rho_package_hashes:
                raise ReportingError(ReportingErrorCode.DUPLICATE_PACKAGE)

        Reporting.ensure_valid_report_result(state,block)
        # Check core assignments
        Reporting.ensure_correct_assignments(state, block)
        Reporting.ensure_signature(state, block)

        # Context anchor block must be present in Beta
        for report in all_reports:
            context = report.context

            found_anchor = False
            for recent_block in state.beta:
                if recent_block.header_hash == context.anchor:
                    if context.beefy_root != MMRFunctions().super_peak(recent_block.mmr):
                        raise ReportingError(
                            ReportingErrorCode.BAD_BEEFY_MMR_ROOT
                        )
                    if recent_block.state_root != context.state_root:
                        raise ReportingError(
                            ReportingErrorCode.BAD_STATE_ROOT,
                            f""
                        )
                    found_anchor = True
            if not found_anchor:
                raise ReportingError(
                    ReportingErrorCode.ANCHOR_NOT_RECENT,
                    "Anchor not found in beta"
                )

            if int(context.lookup_anchor_slot) < int(block.header.slot) - LOOKUP_ANCHOR_MAX_AGE:
                raise ReportingError(
                    ReportingErrorCode.ANCHOR_NOT_RECENT,
                    "Lookup anchor older than max age"
                )

            # --------------- segment_root_lookup_invalid -------------------
            # 11.40
            # https://graypaper.fluffylabs.dev/#/85129da/15ca0115cd01?v=0.6.3
            for lookup, exports_root in report.segment_root_lookup.items():
                if lookup not in recent_exports_roots or recent_exports_roots[lookup] != exports_root:
                    raise ReportingError(
                        ReportingErrorCode.SEGMENT_ROOT_LOOKUP_INVALID,
                        "Work-packages mentioned in the segment-root lookup, be either in the extrinsic or in our recent history."
                    )

            # --------------- dependency_missing -------------------
            # https://graypaper.fluffylabs.dev/#/85129da/15ca0115cd01?v=0.6.3
            # Eq 11.39
            all_prerequisites = [*report.segment_root_lookup.keys(), *context.prerequisites]
            for prereq in all_prerequisites:
                if prereq not in wp_hash_set and prereq not in beta_wp_hashes and prereq not in known_packages:
                    raise ReportingError(
                        ReportingErrorCode.DEPENDENCY_MISSING,
                        "prerequisite's hash should match the package_specification's hash of any of the reports"
                    )




        # for i in state.beta:
        #     if any(key in hashes for key in i.packages.keys()):
        #         raise ReportingError(
        #             ReportingErrorCode.DUPLICATE_PACKAGE,
        #             "Work package is already executed in recent-block's history"
        #         )

        #--------------------------duplicated_package_in_reports----------------------------
        # https://graypaper.fluffylabs.dev/#/85129da/151e01152501?v=0.6.3
        if len(block.extrinsic.guarantees) > 1:
            for x in range (len(block.extrinsic.guarantees)):
                for y in range(x+1, len(block.extrinsic.guarantees)):
                    if block.extrinsic.guarantees[x].report.package_spec.hash == block.extrinsic.guarantees[y].report.package_spec.hash:
                        raise ReportingError(
                            ReportingErrorCode.DUPLICATE_PACKAGE,
                            "Duplicate package spec hash in other report of same guarantee"
                        )


        # 11.32
        if len(wp_hash_set) != len(all_reports):
            raise ReportingError(
                ReportingErrorCode.DUPLICATE_PACKAGE,
                f"Duplicate Work Package detected"
            )

        pi_core = AllCoreStats.empty()
        pi_service = AllServiceStats({})

        rho = state.rho

        for report in all_reports:
            rho[report.core_index] = OptionalWorkReportState(
                WorkReportState(
                    report=report,
                    timeout=block.header.slot
                )
            )
            core_index = report.core_index
            for result in report.results:
                pi_core[core_index].imports += Int(result.refine_load.imports)
                pi_core[core_index].exports += Int(result.refine_load.exports)
                pi_core[core_index].gas_used += Int(result.refine_load.gas_used)
                pi_core[core_index].extrinsic_count += Int(result.refine_load.extrinsic_count)
                pi_core[core_index].extrinsic_size += Int(result.refine_load.extrinsic_size)
            pi_core[core_index].bundle_size = Int(report.package_spec.length)

            for work_result in report.results:
                if work_result.service_id not in pi_service:
                    pi_service[work_result.service_id] = ServiceStat.empty()
                pi_service[work_result.service_id].refinement_count += 1
                pi_service[work_result.service_id].refinement_gas_used += Int(
                    work_result.refine_load.gas_used
                )
                pi_service[work_result.service_id].imports += Int(work_result.refine_load.imports)
                pi_service[work_result.service_id].exports += Int(work_result.refine_load.exports)
                pi_service[work_result.service_id].extrinsic_count += Int(
                    work_result.refine_load.extrinsic_count
                )
                pi_service[work_result.service_id].extrinsic_size += Int(
                    work_result.refine_load.extrinsic_size
                )

        pi = state.pi
        pi.cores = pi_core
        pi.services = pi_service
        state.pi = pi
        state.rho = rho

        return state

    @staticmethod
    def ensure_signature(state: Sigma, block: Block):
        """
        Description : This function make sure that signature for the work_report is valid (ensure that report are signed by correct validators which are assigned, to that particular core, through guarantor assignment).

        Sources :  https://graypaper.fluffylabs.dev/#/85129da/15250015af00?v=0.6.3
        """
        for x in block.extrinsic.guarantees:
            for y in x.signatures:
                public_key = None
                if x.slot == block.header.slot or x.slot != block.header.slot and floor((block.header.slot - ROTATION_PERIOD) / EPOCH_LENGTH) == floor(block.header.slot / EPOCH_LENGTH):
                    public_key = state.kappa[y.validator_index].ed25519
                elif x.slot != block.header.slot and floor((block.header.slot - ROTATION_PERIOD) / EPOCH_LENGTH) != floor(block.header.slot / EPOCH_LENGTH):
                    public_key = state.lambda_[y.validator_index].ed25519
                signature = y.signature

                # TODO: Uncomment this
                try:
                    Ed25519PublicKey.from_public_bytes(
                        bytes(public_key)
                    ).verify(
                        bytes(signature),
                        SIGNING_CONTEXTS['guarantee'] + bytes(Hash.blake2b(x.report.encode()))
                    )
                except InvalidSignature:
                    raise ReportingError(
                        ReportingErrorCode.BAD_SIGNATURE,
                        "Signature doesn't match with that particular public key"
                    )

    @staticmethod
    def verify_report_output(report: WorkReport):
        """
        Description: ensure that work report (authorizer output + sum of report output ) size always should be <= 48*(2**10)

        Source: https://graypaper.fluffylabs.dev/#/85129da/141d00144500?v=0.6.3

        """
        work_report_output = len(report.auth_output)
        for result in report.results:
            # TODO - Test this with non-OK results
            if result.result.get_key() == "ok":
                work_report_output += len(result.result.get_value())

        if work_report_output > MAX_WORK_REPORT_SIZE:
            raise ReportingError(
                ReportingErrorCode.WORK_REPORT_TOO_BIG,
                "Length of sum of result and auth_output should be less than 48 * 2**10 "
            )

    @staticmethod
    def ensure_valid_report_result(state: Sigma, block: Block):

        """
               Description: This function takes two arguments and checks for all the testcases related to results section of each report.

               Args:
                   state: This is the state on which transition happen or another state to get previous and curr data (like validators)
                   block: This is the recent block (modified according to the input provided in the testcases) to be added on-chain and to get all information(like header, slot, extrinsic)

               Returns:
                   Returns error according to specific testcases.

        """
        results = block.extrinsic.guarantees

        for x in results:
            total_accumulate_gas = 0
            for y in x.report.results:
                # --------------- bad_service_id -------------------
                if y.service_id not in state.delta:
                    raise ReportingError(
                        ReportingErrorCode.BAD_SERVICE_ID,
                        "Service_id of each report should match with id of delta"
                    )
                    
                # --------------- bad_code_hash -------------------
                # https://graypaper.fluffylabs.dev/#/85129da/153302153502?v=0.6.3
                # Eq 11.42
                if y.code_hash != state.delta[y.service_id].service.code_hash:
                    raise ReportingError(
                        ReportingErrorCode.BAD_CODE_HASH,
                        "Result code_hash should match with state's delta code_hash"
                    )
                    
                # --------------- service_item_gas_too_low -------------------
                # https://graypaper.fluffylabs.dev/#/85129da/15f80015fa00?v=0.6.3
                # Eq 11.30
                if y.accumulate_gas < state.delta[y.service_id].service.min_gas:
                    raise ReportingError(
                        ReportingErrorCode.SERVICE_ITEM_GAS_TOO_LOW,
                        "For every report its accumulate gas should be greater than the delta's min_gas"
                    )

                total_accumulate_gas = total_accumulate_gas + y.accumulate_gas
               
            # --------------- work_report_gas_too_high -------------------
            # https://graypaper.fluffylabs.dev/#/85129da/15fa0015fd00?v=0.6.3
            # Eq 11.30
            if total_accumulate_gas > ACCUMULATION_GAS:
                raise ReportingError(
                    ReportingErrorCode.WORK_REPORT_GAS_TOO_HIGH,
                    "Sum of all accumulate gas in result of report should be less than ACCUMULATION_GAS"
                )

    @staticmethod
    def ensure_correct_assignments(state: Sigma, block: Block):
        """
        Description : This function check assign validator to the core is correct or not.

        """
        if len(block.extrinsic.guarantees) == 0:
            # Return if no gurantees to check
            return

        report_slot = None
        for x in block.extrinsic.guarantees:
            report_slot = x.slot

        guarantors_assigned = guarantor_assignment(state.eta, state.kappa, state.lambda_, block.header.slot, report_slot)

        # array of assign validator for each core
        current_assigned: Dict[CoreIndex, Set] = {}
        for x in block.extrinsic.guarantees:
            key = x.report.core_index
            value = set()
            for y in x.signatures:
                value.add(y.validator_index)
            current_assigned[key] = value

        # Iterate through current gurantee assignments, match them against ideal gurantor assigned
        for core, vals in current_assigned.items():
            for validator in vals:
                if validator not in guarantors_assigned[core]:
                    raise ReportingError(
                        ReportingErrorCode.WRONG_ASSIGNMENT,
                        "Assign wrong validator to the core"
                    )
