import dataclasses

from jam.merklization import OptionHash
from jam.state.components.chi import ChiG
from jam.state.components.tau import Tau
from jam.types.protocol.core import Gas,ServiceId,OpaqueHash,Balance
from tests.unit.accumulation.types import DeferredTransfer, AcclOutput, AccCommitmentMap, DeferredTransfers, gasPrivilages, gasPrivilage, StateContext
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.work.report import WorkReport,WorkExecResult,WorkPackageSpec
from jam.state.components.delta import Delta,AccountData
from jam.state.components.iota import Iota
from jam.state.components.xi import Xi
from jam.state.components.chi import Chi,ChiA,ChiG,ChiM,ChiV
import copy
from jam.state.components.nu import Nu, AllReadyWRs, ReadyWR
from jam.state.state import State
from jam.types import Block, Null
from jam.types.work.report import WorkDependencies, WorkReports, SegmentRootLookup
from jam.utils.constants import EPOCH_LENGTH,TOTAL_GAS,ACCUMULATION_GAS,CORE_COUNT

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
            if len(wr.context.prerequisites) == 0 and wr.segment_root_lookup == SegmentRootLookup([]):
                filtered_reports.append(wr)

        return filtered_reports

    @staticmethod
    def queue_creator_fn(work_reports: WorkReports) -> AllReadyWRs:
        """
        Function D defined in Eq 12.6
        Takes work reports & returns queued work reports with dependencies

        Args:
            work_reports: All work reports

        Returns:
            Queued WRs
        """

        queued_wr = AllReadyWRs([])
        for wr in work_reports:
            dependencies = WorkDependencies(wr.context.prerequisites)
            for segment_item in wr.segment_root_lookup:
                dependencies.append(segment_item.work_package_hash)
            work_report = ReadyWR(report=wr, dependencies=dependencies)
            queued_wr.append(work_report)

        return queued_wr

    @staticmethod
    def queue_edit_fn(accumulation_queue: AllReadyWRs, removable_packages: WorkDependencies) -> AllReadyWRs:
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
                updated_queue.append(wr)
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
            if r.dependencies == WorkDependencies([]):
                g.append(r.report)

        if g == WorkReports([]):
            return g

        else:
            g_star = cls.priority_queue_fn(cls.queue_edit_fn(accumulation_queue, cls.mapping_fn(g)))
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
            services: ChiG
    ) -> tuple[int, StateContext, DeferredTransfers, AccCommitmentMap]:
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
        
        Returns:
            A tuple (int, StateContext, DeferredTransfer, AccCommitmentMap) where:
            Integer: Number of work results successfully accumulated.
            StateContext: The updated state context after applying accumulation.
            DeferredTransfer: A list of transfers that are deferred.
            AccCommitmentMap: A mapping of service indices to their corresponding accumulation outputs.
        """
        
        index = 0
        report_gas = 0
        for i in work_reports:
            for j in i.results:
                report_gas += j.accumulate_gas
            if report_gas > gas_limit:
                break
            index=index+1

        if index==0:
            return 0, partial_state, DeferredTransfers([]), AccCommitmentMap([])

        work_reports_start = work_reports[:index]
        [gas_star, partial_state_star, deferred_transfers_star, accl_outputs_star] = Accumulation.parallel_accumulation(partial_state, work_reports_start, services)

        work_reports_end = work_reports[index:]
        gas_diff = gas_limit-gas_star
        [j, partial_state_dash, deferred_transfers, accl_outputs] = Accumulation.seq_accumulation(gas_diff, work_reports_end, partial_state_star, ChiG({}))

        deferred_transfers_star.extend(deferred_transfers)

        for i in accl_outputs:
            if i not in accl_outputs_star:
                accl_outputs_star.append(i)

        return index + j, partial_state_dash, deferred_transfers_star, accl_outputs_star


    @staticmethod
    def parallel_accumulation(
            initial_state: StateContext,
            work_reports: WorkReports,
            services: ChiG
    ) ->  tuple[Gas, StateContext, DeferredTransfers, AccCommitmentMap]:
        """
        Parallelized accumulation function ∆* defined in Eq 12.17
        Non-Sequential, Service-Aggregated Execution Pattern
        Transforms Initial Partial State, Sequence of Work Reports, and Dictionary of services (free, privileged accumulation)
        into Tuple of Total gas utilized in PVM, Posterior state-context, Resultant deferred-transfers and Accumulation-output pairings

        Args:
            initial_state (StateContext): The state context before accumulation, which includes service accounts and other mutable components.
            work_reports (WorkReports): A collection of work reports that are ready to be accumulated.
            services (ChiG): A dictionary of services (by service index) that are set up for free accumulation along with their basic gas allowances.

        Returns:
            A tuple (int, StateContext, DeferredTransfer, AccCommitmentMap) where:
            Integer: Total gas utilized in PVM.
            StateContext: The updated state context after applying accumulation.
            DeferredTransfer: A list of transfers that are deferred.
            AccCommitmentMap: A mapping of service indices to their corresponding accumulation outputs.
        """
        
        s: list[ServiceId] = [] # w_r_s service ids

        u: Gas = 0  # accumulated gas
        accl_output_array: AccCommitmentMap = AccCommitmentMap([]) # accumulation-output pairings (b/B)
        t_cap: DeferredTransfers = DeferredTransfers([])
        state: StateContext = initial_state
        
        for i in work_reports:
            for j in i.results:
                if j.service_id not in s:
                    s.append(j.service_id)

        free_services = [key for key in services]

        for i in free_services:
            if i not in s:
                s.append(i)

        for i in s:
            [updated_partial_state, df_list, accl_output, gas] = Accumulation.single_accumulation(state, work_reports, services, ServiceId(i))
            u+=gas
            if accl_output is not None:
                accl_output_array.append(AcclOutput(service_id=i, hash=accl_output))
            for i in df_list:
                t_cap.append(i)
            state=updated_partial_state

        t_cap.sort(key=lambda x: x.sender)
        d=Delta(state.service_accounts)
        i=Iota(state.validator_keys)
        q=Xi(state.authorizer_keys)
        m=ChiM(state.privileges.m)
        a=ChiA(state.privileges.a)
        v=ChiV(state.privileges.v)
        z=ChiG(state.privileges.g)
        n=Delta({})
        m_set=[]

        [updated_partial_state, df_list, accl_output, gas] = Accumulation.single_accumulation(state,work_reports,services,ServiceId(m))
        x_dash=updated_partial_state.privileges

        [updated_partial_state, df_list, accl_output, gas] = Accumulation.single_accumulation(state,work_reports,services,ServiceId(a))
        i_dash=updated_partial_state.validator_keys

        [updated_partial_state, df_list, accl_output, gas] = Accumulation.single_accumulation(state,work_reports,services,ServiceId(v))
        q_dash=updated_partial_state.authorizer_keys

        for i in s:
            [updated_partial_state, df_list, accl_output, gas] = Accumulation.single_accumulation(state,work_reports,services,ServiceId(i))
            d1 = updated_partial_state.service_accounts
            d2 = copy.deepcopy(d1)
            d_keys = copy.deepcopy(d)
            if i in d_keys:
                d_keys.value.pop(i)
            for j in d_keys:
                if j in d1:
                    d1.value.pop(j)
            for k in d1:
                n[ServiceId(k)] = d1.value[k]
            for i1 in d:
                if i1 not in d2 and i1 not in m_set:
                    m_set.append(i1)

        for i2 in n:
            if i2 not in d:
                d[ServiceId(i2)] = n.value[i2]

        for i3 in m_set:
            if i3 in d:
                d.value.pop(i3)

        state.service_accounts = d
        state.privileges.m = x_dash
        state.validator_keys = i_dash
        state.authorizer_keys = q_dash

        return u, state, t_cap, accl_output_array
    

    @staticmethod
    def single_accumulation(
            initial_state: StateContext,
            work_reports: WorkReports,
            services: ChiG,
            service_id: ServiceId
    )-> tuple[StateContext, DeferredTransfers, OptionHash, Gas]:
        """
        Single-Service accumulation function ∆1 defined in Eq 12.19
        Transforms Initial Partial State, Sequence of Work Reports, Dictionary of services (free, privileged accumulation), and Service index
        into Tuple of Posterior state-context, Sequence of Transfers, Possible Accumulation-outputs and Actual gas utilized in PVM,

        Args:
            initial_state (StateContext): The state context before accumulation, which includes service accounts and other mutable components.
            work_reports (WorkReports): A collection of work reports that are ready to be accumulated.
            services (ChiG): A dictionary of services (by service index) that are set up for free accumulation along with their basic gas allowances.
            service_id (ServiceId): Index of Particular Service

        Returns:
            A tuple (StateContext, DeferredTransfer, AccOutput, Gas) where:
            StateContext: The updated state context after applying accumulation.
            DeferredTransfers: A list of transfers that are deferred.
            AccOutput: Possible accumulation outputs.
            Gas: Actual gas utilized in PVM.
        """

        g=0
        p=[]

        for i in work_reports:
            for j in i.results:
                if j.service_id == service_id:
                    p.append(gasPrivilage(o=j.result, l=j.payload_hash, a=i.auth_output, k=i.package_spec))
        
        for i in services:
            if i==service_id:
                g=services[i]
                break

        for i in work_reports:
            for j in i.results:
                if j.service_id==service_id:
                    g+=j.accumulate_gas

        t = Tau(42)
        [posterior_state, transfers, optional_hash, gas] = Accumulation.psi_a(initial_state, t, service_id, g, p)

        return posterior_state, transfers, optional_hash, gas
        
    @staticmethod
    def psi_a(
            partial_state: StateContext,
            tau: Tau,
            service_id: ServiceId,
            g: Gas,
            p: gasPrivilages
    ) -> tuple[StateContext, DeferredTransfers, OptionHash, Gas]:
        return partial_state, DeferredTransfers([]), OptionHash(Null), g

    @staticmethod
    def psi_t(delta: Delta, time:Tau, service_id: ServiceId, deferred_transfers: DeferredTransfers)-> AccountData:
        return delta

    @staticmethod
    def selection_fn(deferred_transfers: DeferredTransfers, service_id: ServiceId)-> DeferredTransfers:
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
            if i.receiver == service_id:
                service_transfers.append(i)
        return service_transfers
    
    @staticmethod
    def wr_si_specific(pre_state: State,block: Block)-> WorkReports:
        return WorkReports([])

    @classmethod
    def transition(cls, pre_state: State, block: Block):

        # ----------------------
        # Section 12.1: History & Queuing
        # ----------------------

        new_state: State = dataclasses.replace(pre_state)

        nu = new_state.nu # Ready for Accumulation
        xi_union = new_state.xi # Accumulated Packages Hist                                                                                       ory

        work_reports = WorkReports([]) # Latest Work Reports to accumulate
        for rg in block.extrinsic.guarantees:
            work_reports.append(rg.report)

        immediate_reports = cls.filter_wr_fn(work_reports)
        queued_reports = cls.queue_edit_fn(cls.queue_creator_fn(work_reports), xi_union)

        m = block.header.slot % EPOCH_LENGTH

        accumulatable_wr = AllReadyWRs([])

        q_right = nu[m:]
        q_left = nu[:m]

        for wrs in q_right:
            accumulatable_wr.extend(wrs)

        for wrs in q_left:
            accumulatable_wr.extend(wrs)

        accumulatable_wr.extend(queued_reports)
        intermediate_queue = cls.queue_edit_fn(accumulatable_wr, cls.mapping_fn(immediate_reports))
        updated_wrs = cls.priority_queue_fn(intermediate_queue)

        star_work_reports = WorkReports(immediate_reports)
        star_work_reports.extend(updated_wrs)

        # ----------------------
        # Section 12.2 Execution
        # ----------------------

        partial_state = StateContext(service_accounts=pre_state.delta, validator_keys=pre_state.iota, authorizer_keys=pre_state.phi, privileges=pre_state.chi)

        # accumulated_gas accumulated from ChiG_services
        service_gas=0
        for i in pre_state.chi.g:
            service_gas+=pre_state.chi.g[i]

        gas_limit = max(TOTAL_GAS,((ACCUMULATION_GAS*CORE_COUNT)+service_gas))
        [work_accl_no, updated_state, deferred_transfers, commitment_map] = Accumulation.seq_accumulation(Gas(gas_limit), star_work_reports, partial_state, pre_state.chi.g)

        # Update Delta Dagger, Chi, Iota, Phi
        new_state.delta = updated_state.service_accounts
        new_state.chi = updated_state.privileges
        new_state.iota = updated_state.validator_keys
        new_state.phi = updated_state.authorizer_keys


        # ----------------------
        # Section 12.3 Deferred Transfers & State Integration
        # ----------------------

        for s in updated_state.service_accounts:
            specific_transfers = Accumulation.selection_fn(deferred_transfers,s)
            # delta_double_dagger
            updated_state.service_accounts[s] = Accumulation.psi_t(updated_state.service_accounts[s], block.header.slot, s, specific_transfers)

        # Update Delta Double Dagger
        new_state.delta = updated_state.service_accounts

        # Updating Accumulated History, Xi
        new_state.xi[EPOCH_LENGTH-1] =  cls.mapping_fn(star_work_reports)

        for i in range(EPOCH_LENGTH-1):
            new_state.xi[i] = new_state.xi[i+1]

        timeslot_difference = block.header.slot - pre_state.tau

        # Updating Ready Queue, Nu
        for i in range(EPOCH_LENGTH):
            if i == 0:
                new_state.nu[m-i] = cls.queue_edit_fn(queued_reports, new_state.xi[-1])
            elif 1 <= i < timeslot_difference:
                new_state.nu[m-i] = AllReadyWRs([])
            elif i >= timeslot_difference:
                new_state.nu[m-i] = cls.queue_edit_fn(new_state.nu[m-i], new_state.xi[-1])

        return new_state

        # ----------------------
        # Section 12.4 Preimage Integration : In Different Module
        # ----------------------
