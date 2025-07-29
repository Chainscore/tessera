import asyncio
import math
from typing import List

from jam.api.rpc.broker import broker
from jam.types import AllValidatorStats, Sigma, WorkReport
from jam.block.block import Block


from jam.types.state.pi import ServiceStat
from jam.utils.constants import EPOCH_LENGTH, SEGMENT_SIZE
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

        # Publishes updates of the statistics stored in chain state returns blob
        asyncio.create_task(broker.publish("subscribeStatistics", list(pi.encode())))

        return state
