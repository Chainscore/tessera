import copy
import dataclasses
from copy import deepcopy

from jam.merklization import OptionHash
from jam.types import Block, Null
from jam.types.protocol.core import Gas,ServiceId
from tests.unit.accumulation.types import AcclOutput, AccCommitmentMap, DeferredTransfers, StateContext, OperandTuples, OperandTuple
from jam.state.components.delta import Delta, AccountData
from jam.state.components.phi import Phi
from jam.state.components.tau import Tau
from jam.state.components.iota import Iota
from jam.state.components.chi import ChiA, ChiG, ChiM, ChiV
from jam.state.components.nu import AllReadyWRs, ReadyWR
from jam.state.state import State
from jam.types.work.report import WorkDependencies, WorkReports, SegmentRootLookup, WorkReport
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
            services: ChiG,
            timeslot: Tau
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
            timeslot (Tau): Curr TimeSlot τ′

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
        [gas_star, partial_state_star, deferred_transfers_star, accl_outputs_star] = Accumulation.parallel_accumulation(partial_state, work_reports_start, services, timeslot)

        work_reports_end = work_reports[index:]
        gas_diff = gas_limit-gas_star
        [j, partial_state_dash, deferred_transfers, accl_outputs] = Accumulation.seq_accumulation(gas_diff, work_reports_end, partial_state_star, ChiG({}), timeslot)

        deferred_transfers_star.extend(deferred_transfers)

        for i in accl_outputs:
            if i not in accl_outputs_star:
                accl_outputs_star.append(i)

        return index + j, partial_state_dash, deferred_transfers_star, accl_outputs_star


    @staticmethod
    def parallel_accumulation(
            initial_state: StateContext,
            work_reports: WorkReports,
            services: ChiG,
            timeslot: Tau
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
            timeslot (Tau): Curr TimeSlot τ′

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
            [updated_partial_state, df_list, accl_output, gas] = Accumulation.single_accumulation(state, work_reports, services, ServiceId(i), timeslot)
            u+=gas
            if accl_output is not None:
                accl_output_array.append(AcclOutput(service_id=i, hash=accl_output))
            for t in df_list:
                t_cap.append(t)
            state=updated_partial_state

        t_cap.sort(key=lambda x: x.sender)
        d=Delta(state.service_accounts)
        i=Iota(state.validator_keys)
        q=Phi(state.authorizer_keys)
        m=ChiM(state.privileges.m)
        a=ChiA(state.privileges.a)
        v=ChiV(state.privileges.v)
        z=ChiG(state.privileges.g)
        n=Delta({})
        m_set=[]

        [updated_partial_state, df_list, accl_output, gas] = Accumulation.single_accumulation(state, work_reports, services, ServiceId(m), timeslot)
        x_dash=updated_partial_state.privileges

        [updated_partial_state, df_list, accl_output, gas] = Accumulation.single_accumulation(state, work_reports, services, ServiceId(a), timeslot)
        i_dash=updated_partial_state.validator_keys

        [updated_partial_state, df_list, accl_output, gas] = Accumulation.single_accumulation(state, work_reports, services, ServiceId(v), timeslot)
        q_dash=updated_partial_state.authorizer_keys

        for i in s:
            [updated_partial_state, df_list, accl_output, gas] = Accumulation.single_accumulation(state, work_reports, services, ServiceId(i), timeslot)
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
            service_id: ServiceId,
            timeslot: Tau
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
            timeslot (Tau): Curr TimeSlot τ′

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
                    p.append(OperandTuple(o=j.result, l=j.payload_hash, a=i.auth_output, k=i.package_spec.hash))
        
        for i in services:
            if i==service_id:
                g=services[i]
                break

        for i in work_reports:
            for j in i.results:
                if j.service_id==service_id:
                    g+=j.accumulate_gas

        [posterior_state, transfers, optional_hash, gas] = Accumulation.psi_a(initial_state, timeslot, service_id, g, p)

        return posterior_state, transfers, optional_hash, gas
        
    @staticmethod
    def psi_a(
            partial_state: StateContext,
            tau: Tau,
            service_id: ServiceId,
            g: Gas,
            p: OperandTuples
    ) -> tuple[StateContext, DeferredTransfers, OptionHash, Gas]:
        return partial_state, DeferredTransfers([]), OptionHash(Null), g

    @staticmethod
    def psi_t(delta: Delta, time:Tau, service_id: ServiceId, deferred_transfers: DeferredTransfers)-> Delta:
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
        xi_union = WorkDependencies([]) # Accumulated Packages List

        for ep in new_state.xi:
            xi_union.extend(ep)

        # PRINT LINE -------------------
        ixi = []
        for ix in xi_union:
            ixi.append(ix)
        print("Initial Acc Queue", ixi)
        # ------------------------------

        # PRINT LINE -------------------
        ixi = []
        for ix in nu:
            for wr in ix:
                ixi.append(wr.report.package_spec.hash)
            ixi.append("break")
        print("Initial Ready Queue", ixi)
        # ------------------------------

        work_reports = WorkReports([]) # Latest Work Reports to accumulate
        for rg in block.extrinsic.guarantees:
            work_reports.append(rg.report)

        # PRINT LINE -------------------
        pwr = []
        for wr in work_reports:
            pwr.append(wr.package_spec.hash)
        print("Work Reports", pwr)
        # ------------------------------

        print("Work Reports og", work_reports)

        immediate_reports = cls.filter_wr_fn(work_reports)

        # PRINT LINE -------------------
        iwr = []
        for wr in immediate_reports:
            iwr.append(wr.package_spec.hash)
        print("Immediate Reports", iwr)
        # ------------------------------

        queued_wr = AllReadyWRs([])

        for wr in work_reports:
            if len(wr.context.prerequisites) > 0 or wr.segment_root_lookup != SegmentRootLookup([]):
                print("length", wr.segment_root_lookup)
                rq = cls.queue_creator_fn(wr)
                queued_wr.append(rq)

        # PRINT LINE -------------------
        qwr = []
        for wr in queued_wr:
            qwr.append(wr.report.package_spec.hash)
        print("Queued Tmp Reports", qwr)
        print("Queued TmpW Reports", queued_wr)
        # ------------------------------

        queued_reports = cls.queue_edit_fn(queued_wr, xi_union)

        # PRINT LINE -------------------
        qwr = []
        for wr in queued_reports:
            qwr.append(wr.report.package_spec.hash)
        print("Queued Reports", qwr)
        # ------------------------------

        m = block.header.slot % EPOCH_LENGTH

        accumulatable_wr = AllReadyWRs([])

        q_right = nu[m:]
        q_left = nu[:m]

        print("q", q_right, q_left, queued_reports)
        print("m", m)

        for wrs in q_right:
            accumulatable_wr.extend(wrs)

        for wrs in q_left:
            accumulatable_wr.extend(wrs)

        accumulatable_wr.extend(queued_reports)

        # PRINT LINE -------------------
        awr = []
        for wr in accumulatable_wr:
            awr.append(wr.report.package_spec.hash)
        print("Accumulatable Reports", awr)
        # ------------------------------

        # q
        intermediate_queue = cls.queue_edit_fn(accumulatable_wr, cls.mapping_fn(immediate_reports))

        # PRINT LINE -------------------
        iq = []
        for wr in intermediate_queue:
            iq.append((wr.report.package_spec.hash, wr.dependencies))
        print("Intermediate Queue", iq)
        # ------------------------------

        # Q(q)
        updated_wrs = cls.priority_queue_fn(intermediate_queue)

        # PRINT LINE -------------------
        uwr = []
        for wr in updated_wrs:
            uwr.append(wr.package_spec.hash)
        print("Updated WRs", uwr)
        # ------------------------------

        # W! ⌢ Q(q)
        star_work_reports = WorkReports(immediate_reports)
        star_work_reports.extend(updated_wrs)

        # PRINT LINE -------------------
        swr = []
        for wr in star_work_reports:
            swr.append(wr.package_spec.hash)
        print("Star Work Reports", swr)
        # ------------------------------

        # TODO: Testing without on chain accumulation
        # # ----------------------
        # # Section 12.2 Execution
        # # ----------------------
        #
        # partial_state = StateContext(service_accounts=pre_state.delta, validator_keys=pre_state.iota, authorizer_keys=pre_state.phi, privileges=pre_state.chi)
        #
        # # accumulated_gas accumulated from ChiG_services
        # service_gas=0
        # for i in pre_state.chi.g:
        #     service_gas+=pre_state.chi.g[i]
        #
        # gas_limit = max(TOTAL_GAS,((ACCUMULATION_GAS*CORE_COUNT)+service_gas))
        # [work_accl_no, updated_state, deferred_transfers, commitment_map] = Accumulation.seq_accumulation(Gas(gas_limit), star_work_reports, partial_state, pre_state.chi.g, block.header.slot)
        #
        # # Update Delta Dagger, Chi, Iota, Phi
        # new_state.delta = updated_state.service_accounts
        # new_state.chi = updated_state.privileges
        # new_state.iota = updated_state.validator_keys
        # new_state.phi = updated_state.authorizer_keys
        #
        #
        # # ----------------------
        # # Section 12.3 Deferred Transfers & State Integration
        # # ----------------------
        #
        # # Update Delta Double Dagger
        # for s in new_state.delta:
        #     specific_transfers = Accumulation.selection_fn(deferred_transfers,s)
        #     # delta_double_dagger
        #     new_state.delta[s] = Accumulation.psi_t(new_state.delta, block.header.slot, s, specific_transfers)

        # Updating Accumulated History, Xi





        for i in range(EPOCH_LENGTH-1):
            new_state.xi[i] = new_state.xi[i+1]

        new_state.xi[EPOCH_LENGTH-1] =  cls.mapping_fn(star_work_reports)

        # PRINT LINE -------------------
        xir = []
        for vwr in new_state.xi[EPOCH_LENGTH - 1]:
            for wr in vwr:
                xir.append(wr)
            xir.append("Break")

        print("nth xi", xir)
        # ------------------------------

        timeslot_difference = block.header.slot - pre_state.tau
        print("τ′", block.header.slot, "τ", pre_state.tau, "τ′-τ", timeslot_difference)
        # print("m", m)

        # Updating Ready Queue, Nu
        for i in range(EPOCH_LENGTH):
            ind = (m + EPOCH_LENGTH - i) % EPOCH_LENGTH
            # print("m", m, "i", i, "sum", (m+EPOCH_LENGTH-i), "ind", ind)
            if i == 0:
                new_state.nu[ind] = cls.queue_edit_fn(queued_reports, new_state.xi[EPOCH_LENGTH-1])
            elif 1 <= i < timeslot_difference:
                print("run")
                new_state.nu[ind] = AllReadyWRs([])
            elif i >= timeslot_difference:
                # print("idhar run")
                # # PRINT LINE -------------------
                # rq = []
                # for wr in new_state.nu[ind]:
                #     rq.append(wr.report.package_spec.hash)
                #
                # print("old nu ind", rq)
                # # ------------------------------
                new_state.nu[ind] = cls.queue_edit_fn(new_state.nu[ind], new_state.xi[EPOCH_LENGTH-1])
                # # PRINT LINE -------------------
                # rq = []
                # for wr in new_state.nu[ind]:
                #     rq.append(wr.report.package_spec.hash)
                #
                # print("new nu ind", rq)
                # # ------------------------------

        # PRINT LINE -------------------
        rq = []
        for wrq in new_state.nu:
            for wr in wrq:
                rq.append(wr.report.package_spec.hash)
            rq.append("br")

        print("Ready Queue", rq)
        # ------------------------------

        # PRINT LINE -------------------
        wrq = []
        for wr in new_state.xi:
            for wri in wr:
                wrq.append(wri)
            wrq.append("br")

        print("Accumulated Queue", wrq)
        # ------------------------------
        print("Ready v Queue", new_state.nu)

        return new_state

        # ----------------------
        # Section 12.4 Preimage Integration : In Different Module
        # ----------------------
