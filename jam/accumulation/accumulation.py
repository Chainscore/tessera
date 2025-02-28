from jam.state.components.nu import Nu, AllReadyWRs, ReadyWR
from jam.state.state import State
from jam.types import Block
from jam.types.work.report import WorkDependencies, WorkReports, SegmentRootLookup
from jam.utils.constants import EPOCH_LENGTH


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

    @classmethod
    def transition(cls, pre_state: State, block: Block):

        # Section 12.1: History & Queuing

        nu = pre_state.nu # Ready for Accumulation
        xi_union = pre_state.xi # Accumulated Packages History

        work_reports = WorkReports([]) # Latest Work Reports to accumulate
        for rg in block.extrinsic.guarantees:
            work_reports.append(rg.report)

        immediate_reports = cls.filter_wr_fn(work_reports)
        queued_reports = cls.queue_edit_fn(cls.queue_creator_fn(work_reports), xi_union)

        m = block.header.slot % EPOCH_LENGTH

        accumulatable_wr = AllReadyWRs([])

        # for i, q in nu:

        # Section 12.2 Execution


        # Section 12.3 Deferred Transfers & State Integration


        # Section 12.4 Preimage Integration



        ...