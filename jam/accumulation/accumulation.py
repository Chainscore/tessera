# import dataclasses
# from dataclasses import dataclass
from jam.state.components.theta import Theta, AllReadyWRs, ReadyWR
from jam.state.state import State
from jam.types import Block
from jam.types.work.report import WorkDependencies, WorkReports, SegmentRootLookup
from jam.utils.constants import EPOCH_LENGTH,TOTAL_GAS,ACCUMULATION_GAS,CORE_COUNT
from jam.state.components.chi import ChiG
from jam.state.components.tau import Tau
from jam.types.protocol.core import Gas,ServiceId,OpaqueHash,Balance
from tests.unit.accumulation.types import DeferredTransfer,AcclOutputs,stateContext,DeferredTransfers,gasPrivilages
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.work.report import WorkReport,WorkExecResult,WorkPackageSpec

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

    @staticmethod
    def priority_queue_fn(accumulation_queue: AllReadyWRs) -> WorkReports:
        """
        Accumulation Priority Queue Function Q defined in Eq 12.8
        Takes current ready queue & returns prioritized work reports

        Args:
            accumulation_queue: Current Queue

        Returns:
            Prioritized Work Reports in order
        """
        prioritized_queue = WorkReports([])
       
        return prioritized_queue

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
    def SequentialAccumulation(gas_limit: Gas, work_reports: WorkReports ,partial_state: stateContext,freeAccServices: ChiG) -> tuple[int,State,DeferredTransfer,AcclOutputs]:
        """
        Arguments-
        gas_limit (Gas): The total gas available for the accumulation process.
        work_reports (WorkReports): A collection of work reports that are ready to be accumulated.
        partial_state (stateContext): The state before accumulation, which includes service accounts and other mutable components. Refer to stateContext for more details.
        freeAccServices (ChiG): A dictionary of services (by service index) that are set up for free accumulation along with their basic gas allowances.
        
        Returns-
        A tuple (int, State, DeferredTransfer, AcclOutputs) where:
        Integer: Number of work results successfully accumulated.
        State: The updated state after applying accumulation.
        DeferredTransfer: A list of transfers that are deferred to be applied later.
        AcclOutputs: A mapping of service indices to their corresponding accumulation outputs.
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
            return [0,partial_state,[],{}]
        [gas,partial_state,DeferredTransfer,AcclOutputs]=Accumulation.parallelAccumulation(partial_state,work_reports,freeAccServices)
        return [0,partial_state,DeferredTransfer,AcclOutputs]

    
    
    @staticmethod
    def parallelAccumulation(partial_state: stateContext, work_reports: WorkReports,freeAccServices: ChiG) ->  tuple[Gas,stateContext,DeferredTransfers,AcclOutputs]:
        """
        Batch execution: Accumulate work reports grouped by service.
        Args:
            pre_state: Current system state.
            work_reports: Work reports for accumulation.
        Returns:
            Tuple of execution count and remaining reports.
        """
        
        s=[]
        for i in work_reports:
            for j in i.results:
                if j.service_id not in s:
                    s.append(j.service_id)
        free_services = [key for key in freeAccServices]
        for i in free_services:
            if i not in s:
                s.append(i)
        
        
        [partial_state,DeferredTransfer,AcclOutputs,gas]=Accumulation.singleAccumulation(partial_state,work_reports,freeAccServices,ServiceId(1729))
        return [gas,partial_state,DeferredTransfer,AcclOutputs]

    @staticmethod
    def singleAccumulation(partial_state: stateContext,work_reports: WorkReports,freeAccServices: ChiG,service_id: ServiceId)-> tuple[stateContext,DeferredTransfers,OpaqueHash,Gas]:
        g=0
        for i in work_reports:
            for j in i.results:
                if j.service_id==service_id:
                    p=gasPrivilages(o=j.result,l=j.payload_hash,a=i.auth_output,k=i.package_spec.hash)
        
        for i in freeAccServices:
            if i==service_id:
                g=freeAccServices[i]
                break;
        for i in work_reports:
            for j in i.results:
                if j.service_id==service_id:
                    g+=j.accumulate_gas
        t=Tau(42);
        [partial_state,DeferredTransfer,OpaqueHash,Gas]=Accumulation.psiA(partial_state,t,service_id,g,p)
        return [partial_state,DeferredTransfer,OpaqueHash,Gas]
        
    @staticmethod
    def psiA(partial_state: stateContext,Tau:Tau,service_id: ServiceId,g:Gas,p:gasPrivilages) -> tuple[stateContext,DeferredTransfers,OpaqueHash,Gas]:
        return [partial_state, [], None, g]
    
    @staticmethod
    def wr_si_specific(pre_state: State,block: Block)-> WorkReports:
        return WorkReports([])
        
    @classmethod
    def transition(cls, pre_state: State, block: Block):

        # new_state = dataclasses.replace(pre_state)
        # disputes = block.extrinsic.disputes

        # Section 12.1: History & Queuing

        theta = pre_state.theta # Ready for Accumulation
        xi_union = pre_state.xi # Accumulated Packages History
        work_reports = WorkReports([]) # Latest Work Reports to accumulate
        
        for rg in block.extrinsic.guarantees:
            work_reports.append(rg.report)

        immediate_reports = cls.filter_wr_fn(work_reports)
        queued_reports = cls.queue_edit_fn(cls.queue_creator_fn(work_reports), xi_union)

        m = block.header.slot % EPOCH_LENGTH

        accumulatable_wr = AllReadyWRs([])

        q_right = theta[m:]
        q_left = theta[:m]

        for wrs in q_right:
            accumulatable_wr.extend(wrs)

        for wrs in q_left:
            accumulatable_wr.extend(wrs)

        accumulatable_wr.extend(queued_reports)

        star_work_reports = cls.queue_edit_fn(accumulatable_wr, cls.mapping_fn(immediate_reports))
        
        
        
        partial_state = stateContext(service_accounts=pre_state.delta,validator_keys=pre_state.iota,authorizer_keys=pre_state.xi,privileges=pre_state.chi)
        # accumulated_gas accumulated from ChiG_services
        service_gas=0
        for i in pre_state.chi.g:
            service_gas+=pre_state.chi.g[i]
        gaslimit=max(TOTAL_GAS,((ACCUMULATION_GAS*CORE_COUNT)+service_gas))

        # TEST: single service accumulation
        # [partial_state,DeferredTransfer,OpaqueHash,Gas]=Accumulation.singleAccumulation(partial_state,work_reports,pre_state.chi.g,ServiceId(1729))

        # TEST: parallel service accumulation
        
        [gas,partial_state,DeferredTransfer,AcclOutputs]=Accumulation.parallelAccumulation(partial_state,work_reports,pre_state.chi.g)
        
        
        
        # ----------------------
        # Section 12.2 Execution


        # Section 12.3 Deferred Transfers & State Integration


        # Section 12.4 Preimage Integration



        ...