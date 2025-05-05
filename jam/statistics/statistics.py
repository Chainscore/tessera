import math
from copy import deepcopy
from typing import Dict, List

from jam.state.components.pi import (
    AllServiceStats,
    CoreStat,
    ServiceStat,
)
from jam.types.base.integers.fixed import U32
from jam.state.components.pi import ValidatorStat
from jam.state.components.sigma import Sigma
from jam.types.block import Block
from jam.types.protocol.core import Gas, ServiceId
from jam.types.work.report import WorkReport
from jam.utils.constants import CORE_COUNT, EPOCH_LENGTH, SEGMENT_SIZE


def create_empty_validator_stat():
    """Returns a new ValidatorStat object with all values set to 0."""
    return ValidatorStat(
        blocks=0,
        tickets=0,
        pre_images=0,
        pre_images_size=0,
        guarantees=0,
        assurances=0,
    )


def create_empty_core_stat():
    """Returns a new CoreStat object with all values set to 0."""
    return CoreStat(
        gas_used=0,
        imports=0,
        extrinsic_count=0,
        extrinsic_size=0,
        exports=0,
        bundle_size=0,
        da_load=0,
        popularity=0,
    )


def create_empty_service_stat():
    """Returns a new CoreStat object with all values set to 0."""
    return ServiceStat(
        provided_count=0,
        provided_size=0,
        refinement_count=0,
        refinement_gas_used=0,
        imports=0,
        exports=0,
        extrinsic_size=0,
        extrinsic_count=0,
        accumulate_count=0,
        accumulate_gas_used=0,
        on_transfers_count=0,
        on_transfers_gas_used=0,
    )


class Statistics:
    @staticmethod
    def transition(
        pre_state: Sigma,
        block: Block,
        available_wrs: List[WorkReport],
        accumulation_stats: Dict[ServiceId, tuple[Gas, U32]],
        deferred_transfer_stats: Dict[ServiceId, tuple[U32, Gas]],
    ) -> Sigma:
        """
        Transition the state with Statistics logic.

        Args:
            pre_state: State before transition
            block: Block

        Returns:
            State after transition
        """
        new_state = deepcopy(pre_state)

        e = pre_state.tau // EPOCH_LENGTH
        e_dash = block.header.slot // EPOCH_LENGTH

        is_new_epoch = e != e_dash

        if is_new_epoch:
            pi_last = deepcopy(new_state.pi.vals_current)
            pi_curr = deepcopy(new_state.pi.vals_current)

            for i in range(len(pi_curr)):
                pi_curr[i] = create_empty_validator_stat()
        else:
            pi_curr = deepcopy(new_state.pi.vals_current)
            pi_last = deepcopy(new_state.pi.vals_last)

        author_index = block.header.author_index

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

        new_state.pi.vals_current = pi_curr
        new_state.pi.vals_last = pi_last

        incoming_wrs = []

        for report_guarantee in block.extrinsic.guarantees:
            incoming_wrs.append(report_guarantee.report)

        pi_core = []
        for i in range(CORE_COUNT):
            pi_core.append(create_empty_core_stat())

        for report in incoming_wrs:
            if report is not None:
                core_index = report.core_index
                core_stat = pi_core[core_index]
                for result in report.results:
                    core_stat.imports += result.refine_load.imports
                    core_stat.exports += result.refine_load.exports
                    core_stat.gas_used += result.refine_load.gas_used
                    core_stat.extrinsic_count += result.refine_load.extrinsic_count
                    core_stat.extrinsic_size += result.refine_load.extrinsic_size
                core_stat.bundle_size = report.package_spec.length

        for report in available_wrs:
            if report is not None:
                core_index = report.core_index
                core_stat = pi_core[core_index]
                core_stat.da_load = report.package_spec.length + (
                    SEGMENT_SIZE
                    * math.ceil(report.package_spec.exports_count * 65 / 64)
                )

        for assurance in block.extrinsic.assurances:
            for index, bit in enumerate(assurance.bitfield):
                pi_core[index].popularity += 1 if bit else 0

        new_state.pi.cores = pi_core

        r = []
        for report in incoming_wrs:
            for result in report.results:
                r.append(result.service_id)

        p = []
        for preimage in block.extrinsic.preimages:
            if preimage.blob is not None:
                p.append(preimage.requester)

        all_service_ids = (
            set(accumulation_stats.keys())
            | set(deferred_transfer_stats.keys())
            | set(r)
            | set(p)
        )

        pi_service = AllServiceStats({})

        for report in incoming_wrs:
            for work_result in report.results:
                if work_result.service_id in all_service_ids:
                    if work_result.service_id not in pi_service:
                        pi_service[work_result.service_id] = create_empty_service_stat()
                    curr_service_stat = pi_service[work_result.service_id]
                    curr_service_stat.refinement_count += 1
                    curr_service_stat.refinement_gas_used += (
                        work_result.refine_load.gas_used
                    )
                    curr_service_stat.imports += work_result.refine_load.imports
                    curr_service_stat.exports += work_result.refine_load.exports
                    curr_service_stat.extrinsic_count += (
                        work_result.refine_load.extrinsic_count
                    )
                    curr_service_stat.extrinsic_size += (
                        work_result.refine_load.extrinsic_size
                    )

        for preimage in block.extrinsic.preimages:
            if preimage.blob is not None:
                if preimage.requester not in pi_service:
                    pi_service[preimage.requester] = create_empty_service_stat()
                curr_service_stat = pi_service[preimage.requester]
                curr_service_stat.provided_count += 1
                curr_service_stat.provided_size += len(preimage.blob)

        for service_id in accumulation_stats.keys():
            if service_id not in pi_service:
                pi_service[service_id] = create_empty_service_stat()
            pi_service[service_id].accumulate_gas_used = accumulation_stats[service_id][
                0
            ]
            pi_service[service_id].accumulate_count = accumulation_stats[service_id][1]

        for service_id in deferred_transfer_stats.keys():
            if service_id not in pi_service:
                pi_service[service_id] = create_empty_service_stat()
            pi_service[service_id].on_transfers_count = deferred_transfer_stats[
                service_id
            ][0]
            pi_service[service_id].on_transfers_gas_used = deferred_transfer_stats[
                service_id
            ][1]

        new_state.pi.services = pi_service

        return new_state
