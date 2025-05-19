from copy import deepcopy
from typing import Tuple, List, Set

from jam.execution.host_calls.invocations.accumulate import PsiA
from jam.types.base import Bytes, Null
from jam.types.block import Block
from jam.accumulation.types import (
    PreimageDict,
    GasAccumulations,
    AccumulationOutput,
    DeferredTransfers,
    StateContext,
    OperandTuples,
    OperandTuple,
)
from jam.types.protocol.crypto import Hash, OpaqueHash

from jam.types.state.sigma import Sigma
from jam.types.state.delta import Delta, LookupTable, Timestamps
from jam.types.state.tau import Tau
from jam.types.state.chi import ChiA, ChiG, ChiM, ChiV
from jam.types.state.nu import AllReadyWRs, ReadyWR
from jam.utils.constants import EPOCH_LENGTH,TOTAL_GAS,ACCUMULATION_GAS,CORE_COUNT
from jam.types.protocol.merkle import OptionHash
from jam.types.protocol.core import Gas, ServiceId, TimeSlot
from jam.types.work.report import (
    WorkDependencies,
    WorkReports,
    SegmentRootLookup,
    WorkReport,
)
from jam.utils.constants import EPOCH_LENGTH

GasConsumed = List[Tuple[ServiceId, Gas]]
BeefyMap = Set[Tuple[ServiceId, OpaqueHash]]

class Accumulation:
    @staticmethod
    def filter_wr_fn(work_reports: WorkReports) -> WorkReports:
        """
        Utility Function for W!
        Takes work reports & returns filtered reports

        Args:
            work_reports: All work reports

        Returns:
            Filtered WRs
        """

        filtered_reports = WorkReports([])

        for wr in work_reports:
            if len(
                wr.context.prerequisites
            ) == 0 and len(wr.segment_root_lookup) == 0:
                filtered_reports.append(wr)

        return filtered_reports

    @staticmethod
    def queue_creator_fn(work_report: WorkReport) -> ReadyWR:
        """
        Function D defined in Eq 12.6
        Takes work report & returns ready work report with dependencies

        Args:
            work_report: work report

        Returns:
            Ready WR
        """

        dependencies = deepcopy(work_report.context.prerequisites)
        for segment_item in work_report.segment_root_lookup:
            if segment_item.work_package_hash not in dependencies:
                dependencies.append(segment_item.work_package_hash)

        ready_wr = ReadyWR(report=work_report, dependencies=dependencies)

        return ready_wr

    @staticmethod
    def queue_edit_fn(
        accumulation_queue: AllReadyWRs, removable_packages: WorkDependencies
    ) -> AllReadyWRs:
        """
        Queue Editing Function E defined in Eq 12.7
        Takes current ready queue and removes specified packages from the queue

        Args:
            accumulation_queue: Current Queue
            removable_packages: Already accumulated packages / packages to remove from queue

        Returns:
            Updated WR Queue
        """

        updated_queue = AllReadyWRs([])
        for wr in accumulation_queue:
            if wr.report.package_spec.hash not in removable_packages:
                dependencies = WorkDependencies([])
                for dep in wr.dependencies:
                    if dep not in removable_packages:
                        dependencies.append(dep)

                updated_wr = ReadyWR(report=wr.report, dependencies=dependencies)
                updated_queue.append(updated_wr)

        return updated_queue

    @classmethod
    def priority_queue_fn(cls, accumulation_queue: AllReadyWRs) -> WorkReports:
        """
        Accumulation Priority Queue Function Q defined in Eq 12.8
        Takes current ready queue & returns prioritized work reports

        Args:
            accumulation_queue: Current Queue

        Returns:
            Prioritized Work Reports in order
        """

        g = WorkReports([])
        for r in accumulation_queue:
            if len(r.dependencies) == 0:
                g.append(r.report)

        if len(g) == 0:
            return g

        else:
            g_star = cls.priority_queue_fn(
                cls.queue_edit_fn(accumulation_queue, cls.mapping_fn(g))
            )
            g.extend(g_star)

            return g

    @staticmethod
    def mapping_fn(work_reports: WorkReports) -> WorkDependencies:
        """
        Mapping Function P defined in Eq 12.9
        Takes Work Reports and extracts corresponding work package hashes

        Args:
            work_reports: Set of Work reports

        Returns:
            Set of Work Package hashes
        """

        pacakge_hashes = WorkDependencies([])

        for wr in work_reports:
            pacakge_hashes.append(wr.package_spec.hash)

        return pacakge_hashes

    @staticmethod
    def seq_accumulation(
        gas_limit: Gas,
        work_reports: WorkReports,
        partial_state: StateContext,
        services: ChiG,
        timeslot: Tau,
    ) -> tuple[int, StateContext, DeferredTransfers, BeefyMap, GasConsumed]:
        """
        Outer accumulation function ∆+ defined in Eq 12.16
        Sequential Execution Pattern
        Transforms Gas Limit, Sequence of Work Reports, Initial Partial State and Dictionary of services (free, privileged accumulation)
        into Tuple of No. of Work Reports accumulated, Posterior state-context, Resultant deferred-transfers and Accumulation-output pairings

        Args:
            gas_limit (Gas): The total gas available for the accumulation process.
            work_reports (WorkReports): A collection of work reports that are ready to be accumulated.
            partial_state (StateContext): The state context before accumulation, which includes service accounts and other mutable components.
            services (ChiG): A dictionary of services (by service index) that are set up for free accumulation along with their basic gas allowances.
            timeslot (Tau): Curr TimeSlot τ′

        Returns:
            A tuple (int, StateContext, DeferredTransfer, AccumulationOutput) where:
            Integer: Number of work results successfully accumulated.
            StateContext: The updated state context after applying accumulation.
            DeferredTransfer: A list of transfers that are deferred.
            AccumulationOutput: A mapping of service indices to their corresponding accumulation outputs.
        """

        index = 0
        report_gas = 0
        for i in work_reports:
            for j in i.results:
                report_gas += j.accumulate_gas
            if report_gas > gas_limit:
                break
            index = index + 1

        if index == 0:
            return 0, partial_state, DeferredTransfers([]), set(), []

        work_reports_start = work_reports[:index+1]

        partial_state, transfers, outputs, gas_consumed = (
            Accumulation.parallel_accumulation(
                partial_state, work_reports_start, services, timeslot
            )
        )

        work_reports_end = work_reports[index:]
        gas_star = Gas(0)
        for _, gas in gas_consumed:
            gas_star += gas
        gas_diff = gas_limit - gas_star

        j, partial_state, r_transfers, r_outputs, r_gas_consumed = (
            Accumulation.seq_accumulation(
                gas_diff, work_reports_end, partial_state, ChiG({}), timeslot
            )
        )

        transfers.extend(r_transfers)
        gas_consumed.extend(r_gas_consumed)
        outputs.update(r_outputs)

        return index + j, partial_state, transfers, outputs, gas_consumed

    @staticmethod
    def parallel_accumulation(
        partial_state: StateContext,
        work_reports: WorkReports,
        privileged_services: ChiG,
        timeslot: Tau,
    ) -> Tuple[StateContext, DeferredTransfers, BeefyMap, GasConsumed]:
        """
        Parallelized accumulation function ∆* defined in Eq 12.17
        Non-Sequential, Service-Aggregated Execution Pattern
        Transforms Initial Partial State, Sequence of Work Reports, and Dictionary of services (free, privileged accumulation)
        into Tuple of Total gas utilized in PVM, Posterior state-context, Resultant deferred-transfers and Accumulation-output pairings

        Args:
            partial_state (StateContext): The state context before accumulation, which includes service accounts and other mutable components.
            work_reports (WorkReports): A collection of work reports that are ready to be accumulated.
            privileged_services (ChiG): A dictionary of services (by service index) that are set up for free accumulation along with their basic gas allowances.
            timeslot (Tau): Curr TimeSlot τ′

        Returns:
            A tuple (int, StateContext, DeferredTransfer, AccumulationOutput) where:
            Integer: Total gas utilized in PVM.
            StateContext: The updated state context after applying accumulation.
            DeferredTransfer: A list of transfers that are deferred.
            AccumulationOutput: A mapping of service indices to their corresponding accumulation outputs.
        """

        # All service IDs to accumulate
        # s in 12.17
        services: Set[ServiceId] = {
            result.service_id
            for report in work_reports
            for result in report.results
        }
        services.update(privileged_services.keys())

        # Accumulated gas by each service
        # u in 12.17
        gas_consumed: GasConsumed = []

        # Accumulation output hashes
        # b in 12.17
        outputs: BeefyMap = set()

        # Deferred transfers
        # t_telda in 12.17
        transfers = DeferredTransfers([])


        collected_preimages: Set[Tuple[ServiceId, Bytes]] = set()

        for service in services:
            partial_state, _transfers, _output_hash, _gas_consumed, _preimages = Accumulation.single_accumulation(
                partial_state, work_reports, privileged_services, service, timeslot
            )
            gas_consumed.append((service,_gas_consumed))
            # print("_output_hash", _output_hash.get_value(), _output_hash.get_value() is not None, _output_hash is not None, _output_hash != Null, _output_hash.get_value() != Null)
            if _output_hash != Null:
                outputs.add((service, _output_hash.get_value()))
            transfers.extend(_transfers)
            collected_preimages.update(_preimages)

        Accumulation.preimage_integration(partial_state.service_accounts, collected_preimages, timeslot)

        return partial_state, transfers, outputs, gas_consumed

    @staticmethod
    def single_accumulation(
        initial_state: StateContext,
        work_reports: WorkReports,
        services: ChiG,
        service_id: ServiceId,
        timeslot: Tau,
    ) -> tuple[StateContext, DeferredTransfers, OptionHash, Gas, PreimageDict]:
        """
        Single-Service accumulation function ∆1 defined in Eq 12.19
        Transforms Initial Partial State, Sequence of Work Reports, Dictionary of services (free, privileged accumulation), and Service index
        into Tuple of Posterior state-context, Sequence of Transfers, Possible Accumulation-outputs and Actual gas utilized in PVM,

        Args:
            initial_state (StateContext): The state context before accumulation, which includes service accounts and other mutable components.
            work_reports (WorkReports): A collection of work reports that are ready to be accumulated.
            services (ChiG): A dictionary of services (by service index) that are set up for free accumulation along with their basic gas allowances.
            service_id (ServiceId): Index of Particular Service
            timeslot (Tau): Curr TimeSlot τ′

        Returns:
            A tuple (StateContext, DeferredTransfer, AccOutput, Gas) where:
            StateContext: The updated state context after applying accumulation.
            DeferredTransfers: A list of transfers that are deferred.
            AccOutput: Possible accumulation outputs.
            Gas: Actual gas utilized in PVM.
        """

        g = 0
        p = OperandTuples([])

        for i in work_reports:
            for j in i.results:
                if j.service_id == service_id:
                    p.append(
                        OperandTuple(
                            d=j.result,
                            g=j.accumulate_gas,
                            y=j.payload_hash,
                            o=i.auth_output,
                            e=i.package_spec.exports_root,
                            h=i.package_spec.hash,
                            a=i.auth_output
                        )
                    )

        for i in services:
            if i == service_id:
                g = services[i]
                break

        for i in work_reports:
            for j in i.results:
                if j.service_id == service_id:
                    g += j.accumulate_gas
        posterior_state, transfers, optional_hash, gas, preimage = PsiA(u=initial_state, t=timeslot, s=service_id, g=g, o=p).execute()

        return posterior_state, transfers, optional_hash, gas, preimage

    @staticmethod
    def preimage_integration(accounts: Delta, preimages: Set[Tuple[ServiceId, Bytes]], timeslot: Tau) -> Delta:
        """
        Preimage integration function - transforms a dictionary of service states and a set of service/hash pairs
        into a new dictionary of service states
        Args:
            timeslot: current timeslot
            accounts: Delta
            preimages: (ServiceId, Bytes)

        Returns:
            updated_accounts: Delta
        """
        for service_id, blobs in preimages:
            service = accounts[service_id]
            if service is None:
                raise ValueError("[Accumulation] Unexpected: Received preimage for a service that does not exist")
            key_hash = Hash.blake2b(blobs)
            lookup = LookupTable(key_hash, len(blobs))
            if len(service.timestamps[lookup]) == 0:
                service.timestamps[lookup] = Timestamps([timeslot])
                service.lookup[key_hash] = blobs

    @staticmethod
    def selection_fn(
        deferred_transfers: DeferredTransfers, delta: Delta
    ) -> DeferredTransfers:
        """
        Selection function R defined in Eq 12.23
        Maps a sequence of deferred transfers & a desired destination service index
        into sequence of transfers targeting said service

        Args:
            deferred_transfers (DeferredTransfers): Sequence of deferred transfers.
            service_id (ServiceId): Index of Particular Service

        Returns:
            DeferredTransfers: A list of ordered, deferred transfers.
        """

        service_transfers = DeferredTransfers([])
        for i in deferred_transfers:
            if i.receiver in delta:
                service_transfers.append(i)
        return service_transfers

    @classmethod
    def transition(cls, pre_state: Sigma, block: Block):
        """
        Transition the state's Delta, Xi, Nu, Chi, Iota, Phi components, calculate BEEFY Commitment Map.
        Includes 4 steps

        Step 1:
            Filter work reports into immediately-accumulatable reports and to-be-queued reports
            Defined in eqn 12.4 - 12.5

        Step 2:
            Process to-be-queued reports and update ready to be accumulated work reports
            Defined in eqn 12.11

        Step 3:
            Accumulate the reports & update the Chi, Delta, Iota, Phi state components
            Defined in eqn 12.21 - 12.24

        Step 4:
            Update accumulation and ready queues, i.e., Xi, Nu state components
            Defined in eqn 12.25 - 12.27

        Source:
            https://graypaper.fluffylabs.dev/#/85129da/159902159902?v=0.6.3

        Args:
            pre_state: State before transition
            block: Block

        Returns:
            State after transition
        """

        # ----------------------
        # Section 12.1: History & Queuing (Step 1 & 2)
        # ----------------------

        new_state = pre_state

        # Ready Queue
        nu = new_state.nu

        # Accumulated Queue
        xi_union = WorkDependencies([])

        for ep in new_state.xi:
            xi_union.extend(ep)

        # Latest Work Reports to Process
        work_reports = WorkReports([])
        for rg in block.extrinsic.guarantees:
            work_reports.append(rg.report)

        # Reports to be processed Immediately, Eq 12.4
        immediate_reports = cls.filter_wr_fn(work_reports)

        queued_wr = AllReadyWRs([])

        for wr in work_reports:
            if len(
                wr.context.prerequisites
            ) > 0 or len(wr.segment_root_lookup) == 0:
                rq = cls.queue_creator_fn(wr)
                queued_wr.append(rq)

        # Reports to be queued, Eq 12.5
        queued_reports = cls.queue_edit_fn(queued_wr, xi_union)

        # Calculate current timeslot index, Eq 12.10
        m = block.header.slot % EPOCH_LENGTH

        accumulatable_wr = AllReadyWRs([])

        q_right = nu[m:]
        q_left = nu[:m]

        for wrs in q_right:
            accumulatable_wr.extend(wrs)

        for wrs in q_left:
            accumulatable_wr.extend(wrs)

        accumulatable_wr.extend(queued_reports)

        # Calculate available wrs queue, q, Eq 12.12
        intermediate_queue = cls.queue_edit_fn(
            accumulatable_wr, cls.mapping_fn(immediate_reports)
        )

        # Calculate accumulatable wrs queue, Q(q)
        accumulatable_wrs = cls.priority_queue_fn(intermediate_queue)

        # Evaluate ready to accumulate WRs, W! ⌢ Q(q), Eq 12.11
        star_work_reports = WorkReports([])
        star_work_reports.extend(immediate_reports)
        star_work_reports.extend(accumulatable_wrs)

        # TODO: Testing without on chain accumulation
        # ----------------------
        # Section 12.2 Execution (Step 3)
        # ----------------------

        partial_state = StateContext(service_accounts=pre_state.delta, validator_keys=pre_state.iota, authorizer_keys=pre_state.phi, privileges=pre_state.chi)

        # accumulated_gas accumulated from ChiG_services
        service_gas=0
        for i in pre_state.chi.chi_g:
            service_gas+=pre_state.chi.chi_g[i]

        gas_limit = max(TOTAL_GAS,((ACCUMULATION_GAS*CORE_COUNT)+service_gas))
        [work_accl_no, updated_state, deferred_transfers, commitment_map, gas_accumulations] = Accumulation.seq_accumulation(Gas(gas_limit), star_work_reports, partial_state, pre_state.chi.chi_g, block.header.slot)

        # Update Delta Dagger, Chi, Iota, Phi
        # new_state.delta = updated_state.service_accounts
        new_state.chi = updated_state.privileges
        new_state.iota = updated_state.validator_keys
        new_state.phi = updated_state.authorizer_keys

        # ----------------------
        # Section 12.3 Deferred Transfers & State Integration (Step 4)
        # ----------------------

        # Update Delta Double Dagger
        specific_transfers = Accumulation.selection_fn(deferred_transfers,new_state.delta)

        # for s in new_state.delta:
        #     specific_transfers = Accumulation.selection_fn(deferred_transfers,s)
            # delta_double_dagger
            # new_state.delta[s] = Accumulation.psi_t(new_state.delta, block.header.slot, s, specific_transfers)
            # TODO uncomment
            # new_state.delta[s] = PsiT(d=new_state.delta, t=block.header.slot, s=s, bold_t=specific_transfers).process()

        # Update Accumulated History, Xi
        for i in range(EPOCH_LENGTH - 1):
            new_state.xi[i] = new_state.xi[i + 1]

        new_state.xi[EPOCH_LENGTH - 1] = cls.mapping_fn(star_work_reports)

        timeslot_difference = block.header.slot - pre_state.tau

        # Update Ready Queue, Nu
        for i in range(EPOCH_LENGTH):
            ind = (m + EPOCH_LENGTH - i) % EPOCH_LENGTH
            if i == 0:
                new_state.nu[ind] = cls.queue_edit_fn(
                    queued_reports, new_state.xi[EPOCH_LENGTH - 1]
                )
            elif 1 <= i < timeslot_difference:
                new_state.nu[ind] = AllReadyWRs([])
            elif i >= timeslot_difference:
                new_state.nu[ind] = cls.queue_edit_fn(
                    new_state.nu[ind], new_state.xi[EPOCH_LENGTH - 1]
                )

        # ----------------------
        # Section 12.4 Preimage Integration : In Different Module
        # ----------------------

        return new_state