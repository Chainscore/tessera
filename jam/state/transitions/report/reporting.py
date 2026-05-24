from jam.models import ValidatorIndex
from math import floor
from typing import Set, List

from tsrkit_types import Bytes, Uint, Null

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from jam.block import Block
from jam.log_setup import logger
from jam.state.transitions.report.error import ReportingError, ReportingErrorCode
from jam.state.transitions.report.guarantee_assignment import assign_fn
from jam.models.state.pi import AllCoreStats, ServiceStat, AllServiceStats
from jam.models.state.rho import WorkReportState, OptionalWorkReportState
from jam.models.state.sigma import Sigma
from jam.models.state.alpha import Alpha, AuthorizationPool
from jam.models.state.phi import Phi, AuthorizationQueue
from jam.models.protocol.crypto import OpaqueHash
from jam.models.work import WorkReport
from jam.utils.constants import ACCUMULATION_GAS, MAX_DEPENDENCIES, LOOKUP_ANCHOR_MAX_AGE, X
from jam.utils.constants import (
    VALIDATOR_COUNT,
    CORE_COUNT,
    EPOCH_LENGTH,
    ROTATION_PERIOD,
    MAX_WORK_REPORT_SIZE,
    MAX_AUTH_QUEUE_ITEMS,
    O,
)


class Reporting:
    @staticmethod
    def transition(
        pre_state: Sigma,
        state: Sigma,
        block: Block,
        known_packages: List[OpaqueHash] = [],
    ) -> Sigma:
        """
        Description:
            This function takes two arguments: state, block. This transition function check all the boundary cases for work_report and update the state Rho.
        Args:
            state: This is the state on which transition happen or another state to get previous and curr data (like validators)
            block: This is the recent block added on-chain and to get all information(like header, slot, extrinsic)
            known_packages: Packages from known queue (Omega), accumulation history (Xi)

        Returns:
            Returns the updated Rho(workreport, timeslot)
        """

        pre_omega = pre_state.omega
        pre_xi = pre_state.xi
        rho = state.rho

        # Work package hashes form Omega and Xi
        known_packages = set(known_packages)
        for epoch_queue in pre_omega:
            for queue_el in epoch_queue:
                known_packages.add(queue_el.report.package_spec.hash)
        for deps in pre_xi:
            known_packages.update(deps)

        # small w
        all_reports = []
        wp_hash_set: set[Bytes] = set()
        recent_exports_roots = {}

        # First we loop through all guarantees to check their validity
        for guarantee in block.extrinsic.guarantees:
            report = guarantee.report
            # -------- Too Many Dependencies ---------
            # As defined in - https://graypaper.fluffylabs.dev/#/38c4e62/137b02137b02?v=0.7.0
            segment_root = len(report.segment_root_lookup)
            prerequisite = len(report.context.prerequisites)
            if (segment_root + prerequisite) > MAX_DEPENDENCIES:
                raise ReportingError(
                    ReportingErrorCode.TOO_MANY_DEPENDENCIES,
                    "Work report has many dependencies(segment_lookup + prerequisite)",
                )

            Reporting.verify_report_output(report)

            #  ------- Valid Core Index -----------------
            if report.core_index >= CORE_COUNT:
                raise ReportingError(
                    ReportingErrorCode.BAD_CORE_INDEX,
                    "Core index value is more then core range(CORE_COUNT)",
                )

            # -------- Check if the core already has pending report -------------
            # Ensure Rho is empty for this report
            # 11.29
            # Debug Rho
            rho_val = rho[report.core_index].unwrap()
            if rho_val != Null:
                print(f"DEBUG: Core {report.core_index} ENGAGED! Value: {rho_val}")
                raise ReportingError(
                    ReportingErrorCode.CORE_ENGAGED,
                    "The core index mentioned in report should be available in rho",
                )

            # --------- If the guarantee has enough signatures ------------
            # https://graypaper.fluffylabs.dev/#/38c4e62/150c01152601?v=0.7.0
            credential_len = len(guarantee.signatures)
            if credential_len < 2:
                raise ReportingError(
                    ReportingErrorCode.INSUFFICIENT_GUARANTEE,
                    "Work report doesn't has enough validator guarantees",
                )

            # -------- If the validator index is valid ------------
            for y in guarantee.signatures:
                if y.validator_index >= VALIDATOR_COUNT:
                    raise ReportingError(
                        ReportingErrorCode.BAD_VALIDATOR_INDEX,
                        "Validator index(signature) is out of range",
                    )

            # --------- Guarantees must be sorted ---------
            # 11.25
            # https://graypaper.fluffylabs.dev/#/38c4e62/155c01155c01?v=0.7.0
            for j in range(len(guarantee.signatures) - 1):
                if (
                    guarantee.signatures[j].validator_index
                    >= guarantee.signatures[j + 1].validator_index
                ):
                    raise ReportingError(
                        ReportingErrorCode.NOT_SORTED_OR_UNIQUE_GUARANTORS,
                        "Signature's validator index order is not sorted or are not unique",
                    )

            # --------- not-authorized -----------------
            # https://graypaper.fluffylabs.dev/#/38c4e62/157602158602?v=0.7.0
            # Ensure authorizer hash is present in core's Authorizer Pool
            if report.authorizer_hash not in pre_state.alpha[report.core_index]:
                raise ReportingError(
                    ReportingErrorCode.CORE_UNAUTHORIZED,
                    "Work Report's authorizer_hash not exist in AuthorizationPool",
                )

            # ---------- future_report_slot -----------------
            if guarantee.slot > block.header.slot:
                raise ReportingError(
                    ReportingErrorCode.FUTURE_REPORT_SLOT,
                    "Report's slot more then block's slot",
                )

            # -------- report_epoch_before_last ------------
            if guarantee.slot != block.header.slot:
                # https://graypaper.fluffylabs.dev/#/38c4e62/15d80115e301?v=0.7.0
                last_rotation_slot = ROTATION_PERIOD * (
                    (int(block.header.slot) // ROTATION_PERIOD) - 1
                )
                if guarantee.slot < last_rotation_slot:
                    raise ReportingError(
                        ReportingErrorCode.REPORT_EPOCH_BEFORE_LAST,
                        "Report must be in current or prior rotation only",
                    )

            # --------------- duplicated_package_in_recent_history ----------------------------
            # https://graypaper.fluffylabs.dev/#/38c4e62/154a03158303?v=0.7.0
            wp_hash_set.add(report.package_spec.hash)
            recent_exports_roots[report.package_spec.hash] = report.package_spec.exports_root
            all_reports.append(report)

        # ------------- out_of_order_guarantee ---------------------
        # 11.23
        # https://graypaper.fluffylabs.dev/#/38c4e62/15fb00152801?v=0.7.0
        guarantee_length = len(block.extrinsic.guarantees)
        if guarantee_length > 1:
            for i in range(len(block.extrinsic.guarantees) - 1):
                if (
                    block.extrinsic.guarantees[i].report.core_index
                    >= block.extrinsic.guarantees[i + 1].report.core_index
                ):
                    raise ReportingError(
                        ReportingErrorCode.OUT_OF_ORDER_GUARANTEE,
                        "Core index for each guarantee is not in unique",
                    )

        beta_wp_hashes = set()

        for x in pre_state.beta.h:
            for wp_hash, exports_root in x.reported.items():
                beta_wp_hashes.add(wp_hash)
                recent_exports_roots[wp_hash] = exports_root
        dependency_packages = wp_hash_set | beta_wp_hashes

        rho_package_hashes = set()
        for pending_wr in pre_state.rho:
            wr = pending_wr.unwrap()
            if wr != Null:
                rho_package_hashes.add(wr.report.package_spec.hash)

        for p in wp_hash_set:
            # Ensure this WP is not previously executed - checking Beta, Omega, Rho, Xi
            # 11.38
            if p in beta_wp_hashes or p in known_packages or p in rho_package_hashes:
                logger.error(
                    "Duplicate work package found",
                    package=p.hex(),
                    found_in_beta_wp_hashes=(p in beta_wp_hashes),
                    found_in_known_packages=(p in known_packages),
                    found_in_rho=(p in rho_package_hashes),
                )
                raise ReportingError(
                    ReportingErrorCode.DUPLICATE_PACKAGE,
                    f"Work report {p.hex()} is found to be a duplicate. Previously either seen in recent history, is already in pending set for reporting or accumulation",
                )

        Reporting.ensure_valid_report_result(state, block)
        Reporting.ensure_correct_assignments(state, block)

        # Context anchor block must be present in Beta
        for report in all_reports:
            context = report.context

            found_anchor = False
            for recent_block in state.beta.h:
                if recent_block.header_hash == context.anchor:
                    if context.beefy_root != recent_block.beefy_root:
                        raise ReportingError(ReportingErrorCode.BAD_BEEFY_MMR_ROOT)
                    if recent_block.state_root != context.state_root:
                        raise ReportingError(ReportingErrorCode.BAD_STATE_ROOT, f"")
                    found_anchor = True

            if not found_anchor:
                raise ReportingError(
                    ReportingErrorCode.ANCHOR_NOT_RECENT, "Anchor not found in beta"
                )

            if int(context.lookup_anchor_slot) < int(block.header.slot) - LOOKUP_ANCHOR_MAX_AGE:
                raise ReportingError(
                    ReportingErrorCode.ANCHOR_NOT_RECENT,
                    "Lookup anchor older than max age",
                )

            # --------------- segment_root_lookup_invalid -------------------
            # 11.40
            # https://graypaper.fluffylabs.dev/#/38c4e62/158d03159003?v=0.7.0
            for lookup, exports_root in report.segment_root_lookup.items():
                if (
                    lookup not in recent_exports_roots
                    or recent_exports_roots[lookup] != exports_root
                ):
                    raise ReportingError(
                        ReportingErrorCode.SEGMENT_ROOT_LOOKUP_INVALID,
                        "Work-packages mentioned in the segment-root lookup, be either in the extrinsic or in our recent history.",
                    )

            # --------------- dependency_missing -------------------
            # https://graypaper.fluffylabs.dev/#/38c4e62/158d03159003?v=0.7.0
            # Eq 11.39
            all_prerequisites = [
                *report.segment_root_lookup.keys(),
                *context.prerequisites,
            ]
            for prereq in all_prerequisites:
                if prereq not in dependency_packages:
                    raise ReportingError(
                        ReportingErrorCode.DEPENDENCY_MISSING,
                        "prerequisite's hash should match the package_specification's hash of any of the reports",
                    )

        # --------------------------duplicated_package_in_reports----------------------------
        # https://graypaper.fluffylabs.dev/#/38c4e62/15bd0215ce02?v=0.7.0
        if len(block.extrinsic.guarantees) > 1:
            for x in range(len(block.extrinsic.guarantees)):
                for y in range(x + 1, len(block.extrinsic.guarantees)):
                    if (
                        block.extrinsic.guarantees[x].report.package_spec.hash
                        == block.extrinsic.guarantees[y].report.package_spec.hash
                    ):
                        raise ReportingError(
                            ReportingErrorCode.DUPLICATE_PACKAGE,
                            "Duplicate package spec hash in other report of same guarantee",
                        )

        # 11.32
        if len(wp_hash_set) != len(all_reports):
            raise ReportingError(
                ReportingErrorCode.DUPLICATE_PACKAGE, "Duplicate Work Package detected"
            )

        Reporting.ensure_signature(state, block)

        pi_core = AllCoreStats.empty()
        pi_service = AllServiceStats({})

        for report in all_reports:
            rho[report.core_index] = OptionalWorkReportState(
                WorkReportState(report=report, timeout=block.header.slot)
            )
            core_index = report.core_index
            for digest in report.digests:
                pi_core[core_index].imports += Uint(digest.refine_load.imports)
                pi_core[core_index].exports += Uint(digest.refine_load.exports)
                pi_core[core_index].gas_used += Uint(digest.refine_load.gas_used)
                pi_core[core_index].extrinsic_count += Uint(digest.refine_load.extrinsic_count)
                pi_core[core_index].extrinsic_size += Uint(digest.refine_load.extrinsic_size)
            pi_core[core_index].bundle_size = Uint(report.package_spec.length)

            for work_digest in report.digests:
                if work_digest.service_id not in pi_service:
                    pi_service[work_digest.service_id] = ServiceStat.empty()
                pi_service[work_digest.service_id].refinement_count += 1
                pi_service[work_digest.service_id].refinement_gas_used += Uint(
                    work_digest.refine_load.gas_used
                )
                pi_service[work_digest.service_id].imports += Uint(work_digest.refine_load.imports)
                pi_service[work_digest.service_id].exports += Uint(work_digest.refine_load.exports)
                pi_service[work_digest.service_id].extrinsic_count += Uint(
                    work_digest.refine_load.extrinsic_count
                )
                pi_service[work_digest.service_id].extrinsic_size += Uint(
                    work_digest.refine_load.extrinsic_size
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

        Sources :  https://graypaper.fluffylabs.dev/#/38c4e62/158501154502?v=0.7.0
        """
        curr_rotation = int(state.tau) // ROTATION_PERIOD
        prev_rotation = curr_rotation - 1
        curr_epoch = int(state.tau) // EPOCH_LENGTH
        has_prev_rotation = int(state.tau) >= ROTATION_PERIOD
        prev_rotation_epoch = (
            (int(state.tau) - ROTATION_PERIOD) // EPOCH_LENGTH
            if has_prev_rotation
            else None
        )

        guarantee_validator_keys = []

        for x in block.extrinsic.guarantees:
            report_rotation = int(x.slot) // ROTATION_PERIOD

            if report_rotation == curr_rotation:
                validator_set = state.kappa
            elif has_prev_rotation and report_rotation == prev_rotation:
                validator_set = (
                    state.kappa if prev_rotation_epoch == curr_epoch else state.lambda_
                )
            else:
                raise ReportingError(
                    ReportingErrorCode.REPORT_EPOCH_BEFORE_LAST,
                    "Report must be in current or prior rotation only",
                )

            validator_keys = {
                y.validator_index: validator_set[y.validator_index].ed25519
                for y in x.signatures
            }
            guarantee_validator_keys.append((x, validator_keys))

            for y in x.signatures:
                public_key = validator_keys[y.validator_index]

                # Handle Offenders
                if public_key in state.psi.offenders:
                    raise ReportingError(
                        ReportingErrorCode.BANNED_VALIDATOR,
                        "Banned validators are not authorized to sign reports.",
                    )

        for x, validator_keys in guarantee_validator_keys:
            for y in x.signatures:
                public_key = validator_keys[y.validator_index]
                signature = y.signature

                try:
                    Ed25519PublicKey.from_public_bytes(bytes(public_key)).verify(
                        bytes(signature),
                        X.GUARANTEE.value + bytes(x.report.hash()),
                    )
                except InvalidSignature:
                    raise ReportingError(
                        ReportingErrorCode.BAD_SIGNATURE,
                        "Signature doesn't match with that particular public key",
                    )

    @staticmethod
    def verify_report_output(report: WorkReport):
        """
        Description: ensure that work report (authorizer output + sum of report output ) size always should be <= 48*(2**10)

        Source: https://graypaper.fluffylabs.dev/#/38c4e62/14b20014dd00?v=0.7.0

        """
        work_report_output = len(report.auth_output)
        for digest in report.digests:
            op = digest.result.unwrap()
            if isinstance(op, Bytes):
                work_report_output += len(op)

        if work_report_output > MAX_WORK_REPORT_SIZE:
            raise ReportingError(
                ReportingErrorCode.WORK_REPORT_TOO_BIG,
                "Length of sum of result and auth_output should be less than 48 * 2**10 ",
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

        delta = state.delta
        for x in results:
            if len(x.report.digests) == 0:
                raise ReportingError(
                    ReportingErrorCode.MISSING_WORK_RESULTS,
                    "Work report must contain at least one result",
                )

            total_accumulate_gas = 0
            for y in x.report.digests:
                # --------------- bad_service_id -------------------
                if y.service_id not in delta:
                    raise ReportingError(
                        ReportingErrorCode.BAD_SERVICE_ID,
                        f"Service ID {y.service_id} not found in state accounts",
                    )

                # --------------- bad_code_hash -------------------
                # https://graypaper.fluffylabs.dev/#/38c4e62/161300162600?v=0.7.0
                # Eq 11.42
                if y.code_hash != delta[y.service_id].service.code_hash:
                    raise ReportingError(
                        ReportingErrorCode.BAD_CODE_HASH,
                        "Result code_hash should match with state's delta code_hash",
                    )

                # --------------- service_item_gas_too_low -------------------
                # https://graypaper.fluffylabs.dev/#/38c4e62/158b0215a302?v=0.7.0
                # Eq 11.30
                if y.accumulate_gas < delta[y.service_id].service.min_gas:
                    raise ReportingError(
                        ReportingErrorCode.SERVICE_ITEM_GAS_TOO_LOW,
                        "For every report its accumulate gas should be greater than the delta's min_gas",
                    )

                total_accumulate_gas = total_accumulate_gas + y.accumulate_gas

            # --------------- work_report_gas_too_high -------------------
            # https://graypaper.fluffylabs.dev/#/38c4e62/158b0215a302?v=0.7.0
            # Eq 11.30
            if total_accumulate_gas > ACCUMULATION_GAS:
                raise ReportingError(
                    ReportingErrorCode.WORK_REPORT_GAS_TOO_HIGH,
                    "Sum of all accumulate gas in result of report should be less than ACCUMULATION_GAS",
                )

    @staticmethod
    def ensure_correct_assignments(state: Sigma, block: Block):
        """
        Description : This function check assign validator to the core is correct or not.

        """
        if len(block.extrinsic.guarantees) == 0:
            # Return if no guarantees to check
            return

        mappings = assign_fn(state)
        for x in block.extrinsic.guarantees:
            report_slot = x.slot

            report_rotation = report_slot // ROTATION_PERIOD
            curr_rotation = state.tau // ROTATION_PERIOD

            if curr_rotation == report_rotation:
                guarantors_assigned = mappings[0]
            else:
                guarantors_assigned = mappings[2]

            core_assignment = guarantors_assigned[x.report.core_index]
            val_assignment: Set[ValidatorIndex] = set()
            for y in x.signatures:
                val_assignment.add(y.validator_index)

            for v in x.signatures:
                if v.validator_index not in core_assignment:
                    raise ReportingError(
                        ReportingErrorCode.WRONG_ASSIGNMENT,
                        f"Assigned wrong validators to core {x.report.core_index}. "
                        f"Expected: {core_assignment}, Reported: {val_assignment}",
                    )
