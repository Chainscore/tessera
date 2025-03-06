# import dataclasses
# from dataclasses import dataclass
from jam.state.components.theta import Theta, AllReadyWRs, ReadyWR
from jam.state.state import State
from jam.types import Block
from jam.types.work.report import WorkDependencies, WorkReports, SegmentRootLookup
from jam.utils.constants import EPOCH_LENGTH
from jam.state.components.chi import ChiG
from jam.types.protocol.core import Gas,ServiceId,OpaqueHash,Balance
from tests.unit.accumulation.types import DeferredTransfer,AcclOutput,stateContext
from jam.types.base.sequences.bytes.bytes import Bytes

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
    def SequentialAccumulation(gas_limit: Gas, work_reports: WorkReports ,partial_state: stateContext,freeAccServices: ChiG) -> tuple[int,State,DeferredTransfer,AcclOutput]:
        """
        Arguments-
        gas_limit (Gas): The total gas available for the accumulation process.
        work_reports (WorkReports): A collection of work reports that are ready to be accumulated.
        partial_state (stateContext): The state before accumulation, which includes service accounts and other mutable components. Refer to stateContext for more details.
        freeAccServices (ChiG): A dictionary of services (by service index) that are set up for free accumulation along with their basic gas allowances.
        
        Returns-
        A tuple (int, State, DeferredTransfer, AcclOutput) where:
        Integer: Number of work results successfully accumulated.
        State: The updated state after applying accumulation.
        DeferredTransfer: A list of transfers that are deferred to be applied later.
        AcclOutput: A mapping of service indices to their corresponding accumulation outputs.
        """
        
        report_gas = 0
        
        for i in work_reports:
            for j in i.results:
                report_gas += j.accumulate_gas
        print("Accumulated Gas: ",report_gas)
        if report_gas==0:
            return [0,partial_state,[],{}]
        

        return [0,partial_state,DeferredTransfer,AcclOutput]


    # @staticmethod
    # def parallelAccumulation(pre_state: State, work_reports: WorkReports) ->  WorkReports:
    #     """
    #     Batch execution: Accumulate work reports grouped by service.
    #     Args:
    #         pre_state: Current system state.
    #         work_reports: Work reports for accumulation.
    #     Returns:
    #         Tuple of execution count and remaining reports.
    #     """
        
        # service_groups = {}  # Group work reports by service
        # for wr in work_reports:
        #     service_id = wr.get_service_id()
        #     if service_id not in service_groups:
        #         service_groups[service_id] = WorkReports([])
        #     service_groups[service_id].append(wr)

        # remaining_reports = WorkReports([])

        # # Execute each service group separately
        # for service_id, reports in service_groups.items():
        #     executed, leftover = Accumulation.singleServiceAcc(pre_state, reports)
        #     total_executed += executed
        #     remaining_reports.extend(leftover)

        # return total_executed, remaining_reports

        
    
        
    
    # @staticmethod
    # def singleServiceAcc(pre_state: State, work_reports: WorkReports) -> tuple[int, WorkReports]:
    #     """
    #     Accumulate work reports for a single service.
    #     Args:
    #         pre_state: Current system state.
    #         work_reports: Work reports assigned to a specific service.
    #     Returns:
    #         Tuple of execution count and remaining work reports (if gas limit exceeded).
    #     """
    #     executed_reports = WorkReports([])
    #     remaining_reports = WorkReports([])

    #     available_gas = pre_state.get_available_gas()

    #     for wr in work_reports:
    #         required_gas = wr
    #         if required_gas <= available_gas:
    #             executed_reports.append(wr)
    #             available_gas -= required_gas
    #         else:
    #             remaining_reports.append(wr)  # Keep reports that couldn't be executed

    #     return remaining_reports

    
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
        
        # acc=cls.SequentialAccumulation(0,work_reports,pre_state,pre_state.)
        
        partial_state = stateContext(service_accounts=pre_state.delta,validator_keys=pre_state.iota,authorizer_keys=pre_state.xi,privileges=pre_state.chi)
        # deferred_transfer = DeferredTransfer(sender=ServiceId(1729),receiver=ServiceId(1729),amount=Balance(12114),memo=Bytes(11894),gas=Gas(10)) # for example Sample
        cls.SequentialAccumulation(0,work_reports,partial_state,pre_state.chi)
        

        # ----------------------
        # Section 12.2 Execution


        # Section 12.3 Deferred Transfers & State Integration


        # Section 12.4 Preimage Integration



        ...