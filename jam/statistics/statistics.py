import math
from typing import Dict, List

from jam.types.base import Int
from jam.types.state.pi import (
    AllServiceStats,
    ServiceStat, AllValidatorStats, AllCoreStats,
)
from jam.types.base.integers.fixed import U32
from jam.types.state.sigma import Sigma
from jam.types.block import Block
from jam.types.protocol.core import Gas, ServiceId
from jam.types.work.report import WorkReport
from jam.utils.constants import EPOCH_LENGTH, SEGMENT_SIZE


class Statistics:
    @staticmethod
    def transition(
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

        e = state.tau // EPOCH_LENGTH
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

        for guarantee in block.extrinsic.guarantees:
            signatures = guarantee.signatures
            for signature in signatures:
                validator_index = signature.validator_index
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
                pi_core[int(core_index)].da_load = Int(report.package_spec.length) + Int(
                    SEGMENT_SIZE
                    * math.ceil(report.package_spec.exports_count * 65 / 64)
                )

        for assurance in block.extrinsic.assurances:
            for index, bit in enumerate(assurance.bitfield):
                pi_core[index].popularity += 1 if bit else 0

        pi.cores = pi_core

        p = []
        for preimage in block.extrinsic.preimages:
            if preimage.blob is not None:
                p.append(preimage.requester)

        pi_service = pi.services
        for preimage in block.extrinsic.preimages:
            if preimage.blob is not None:
                if preimage.requester not in pi_service:
                    pi_service[preimage.requester] = ServiceStat.empty()
                curr_service_stat = pi_service[preimage.requester]
                curr_service_stat.provided_count += 1
                curr_service_stat.provided_size += len(preimage.blob)

        pi.services = pi_service

        state.pi = pi

        return state
