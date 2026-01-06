import asyncio
import math
from typing import List

from jam.types import AllValidatorStats, Sigma, WorkReport
from jam.block.block import Block


from jam.types.state.pi import ServiceStat
from jam.utils.constants import EPOCH_LENGTH, SEGMENT_SIZE, ROTATION_PERIOD
from jam.state.transitions.report.guarantee_assignment import assign_fn
from tsrkit_types import Uint


class Statistics:
    @staticmethod
    def transition(
        pre_state: Sigma,
        state: Sigma,
        block: Block,
        available_wrs: List[WorkReport],
    ) -> Sigma:
        """
        Transition the state with Statistics logic.

        Args:
            state: State before transition
            block: Block
            available_wrs

        Returns:
            State after transition
        """

        e = pre_state.tau // EPOCH_LENGTH
        e_dash = block.header.slot // EPOCH_LENGTH

        is_new_epoch = e_dash > e

        pi = state.pi

        if is_new_epoch:
            pi.vals_last = pi.vals_current
            pi.vals_current = AllValidatorStats.empty()

        pi_curr = pi.vals_current
        pi_last = pi.vals_last

        author_index = block.header.author_index

        # Handle genesis block
        if author_index != 2**16 - 1:
            pi_curr[author_index].blocks += 1
            pi_curr[author_index].tickets += len(block.extrinsic.tickets)
            pi_curr[author_index].pre_images += len(block.extrinsic.preimages)

            for preimage in block.extrinsic.preimages:
                pi_curr[author_index].pre_images_size += len(preimage.blob)
        
        curr_mapping, _, prev_mapping, _ = assign_fn(state)
        
        # Build map for remapping keys to current indices
        kappa_lookup = {v.ed25519: i for i, v in enumerate(state.kappa)}

        reporter_set = set()
        for guarantee in block.extrinsic.guarantees:
            report_slot = guarantee.slot
            block_slot = block.header.slot

            # Determine which mapping to use based on rotation
            is_current_rotation = (report_slot // ROTATION_PERIOD) == (block_slot // ROTATION_PERIOD)
            
            mapping = curr_mapping if is_current_rotation else prev_mapping

            assigned_validators = mapping.get(guarantee.report.core_index, [])
            
            # Create a set for O(1) lookup of assigned validator indices
            assigned_validator_indices = {v for v in assigned_validators}

            for sig in guarantee.signatures:
                # Check 1: Validator must be assigned to this core
                if sig.validator_index in assigned_validator_indices:
                    # If prior rotation (epoch change), map lambda index to kappa index
                    if not is_current_rotation and (report_slot // EPOCH_LENGTH) != (block_slot // EPOCH_LENGTH):
                        # Get pubkey from Lambda (priot validator set)
                        pubkey = state.lambda_[sig.validator_index].ed25519
                        # Add to reporter set if the prior validaor still exists in Kappa
                        # Find index in Kappa
                        if pubkey in kappa_lookup:
                            reporter_set.add(kappa_lookup[pubkey])
                    else:
                        reporter_set.add(sig.validator_index)

        for validator_index in reporter_set:
            pi_curr[validator_index].guarantees += 1

        for assurance in block.extrinsic.assurances:
            validator_index = assurance.validator_index
            pi_curr[validator_index].assurances += 1

        pi.vals_current = pi_curr
        pi.vals_last = pi_last

        pi_core = pi.cores

        for report in available_wrs:
            if report is not None:
                core_index = report.core_index
                pi_core[int(core_index)].da_load = Uint(report.package_spec.length) + Uint(
                    SEGMENT_SIZE * math.ceil(report.package_spec.exports_count * 65 / 64)
                )

        for assurance in block.extrinsic.assurances:
            for index, bit in enumerate(assurance.bitfield):
                pi_core[index].popularity += 1 if bit else 0

        pi.cores = pi_core

        p = []
        for preimage in block.extrinsic.preimages:
            if preimage.blob is not None:
                p.append(preimage.requester)

        state.pi = pi

        return state
