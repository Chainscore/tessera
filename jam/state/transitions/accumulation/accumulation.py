import asyncio
import json
from copy import deepcopy
from typing import Tuple, Set, List
from jam.api.rpc.broker import broker
from jam.execution.invocations.accumulate import PsiA
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import Uint
from tsrkit_types.null import Null
from jam.block import Block
from jam.execution.invocations.on_transfer import PsiT
from jam.finality.finality import Finality
from jam.state.partial import GhostPartial
from jam.types.state.accumulation.types import (
    AccumulationOutput,
    DeferredTransfers,
    OperandTuples,
    OperandTuple,
    BeefyMap,
    GasConsumed,
)
from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.types.state.pi import ServiceStat
from jam.types.state.sigma import Sigma
from jam.types.state.delta import Delta, LookupTable, Timestamps
from jam.types.state.tau import Tau
from jam.types.state.chi import ChiZ
from jam.types.state.omega import AllReadyWRs, ReadyWR
from jam.types.state.theta import Commitment, Theta
from jam.utils.constants import EPOCH_LENGTH, TOTAL_GAS, ACCUMULATION_GAS, CORE_COUNT
from jam.types.protocol.merkle import OptionHash
from jam.types.protocol.core import Gas, ServiceId
from jam.types.work import (
    WorkDependencies,
    WorkReports,
    WorkReport,
)


class Accumulation:
    @staticmethod
    def filter_wr_fn(work_reports: WorkReports) -> WorkReports:
        """
        Utility Function for W!
        Takes work reports & returns filtered reports, Eq 12.4

        Args:
            work_reports: All newly available work reports
        Returns:
            Filtered WRs
        """

        filtered_reports = WorkReports([])

        for wr in work_reports:
            if len(wr.context.prerequisites) == 0 and len(wr.segment_root_lookup) == 0:
                filtered_reports.append(wr)

        return filtered_reports

    @staticmethod
    def fetch_dependencies(work_report: WorkReport) -> ReadyWR:
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
            if segment_item not in dependencies:
                dependencies.append(segment_item)

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

        return WorkDependencies(sorted(pacakge_hashes))

    @staticmethod
    def seq_accumulation(
        gas_limit: Gas,
        work_reports: WorkReports,
        services: ChiZ,
        timeslot: Tau,
    ) -> Tuple[int, DeferredTransfers, BeefyMap, GasConsumed]:
        """
        Outer accumulation function ∆+ defined in Eq 12.16
        Sequential Execution Pattern
        Transforms Gas Limit, Sequence of Work Reports, Initial Partial State and Dictionary of services (free, privileged accumulation)
        into Tuple of No. of Work Reports accumulated, Posterior state-context, Resultant deferred-transfers and Accumulation-output pairings

        Args:
            gas_limit (Gas): The total gas available for the accumulation process.
            work_reports (WorkReports): A collection of work reports that are ready to be accumulated.
            services (ChiZ): A dictionary of services (by service index) that are set up for free accumulation along with their basic gas allowances.
            timeslot (Tau): Curr TimeSlot τ′

        Returns:
            A tuple (int, GhostPartial, DeferredTransfers, BeefyMap, GasConsumed) where:
            Integer: Number of work digests successfully accumulated.
            DeferredTransfer: A list of transfers that are deferred.
            BeefyMap: A mapping of service indices to their corresponding accumulation outputs.
            GasConsumed: Gas consumed by accumulation of each service along iwth their service id
        """

        index = 0
        report_gas = 0
        for i in work_reports:
            for j in i.digests:
                report_gas += j.accumulate_gas
            if report_gas > gas_limit:
                break
            index = index + 1

        if index == 0:
            return 0, DeferredTransfers([]), set(), []

        work_reports_start = work_reports[: index + 1]

        transfers, outputs, gas_consumed = Accumulation.parallel_accumulation(
            work_reports_start, services, timeslot
        )

        work_reports_end = work_reports[index:]
        gas_star = Gas(0)
        for _, gas in gas_consumed:
            gas_star += gas
        gas_diff = gas_limit - gas_star

        j, r_transfers, r_outputs, r_gas_consumed = (
            Accumulation.seq_accumulation(
                gas_diff, work_reports_end, ChiZ({}), timeslot
            )
        )

        transfers.extend(r_transfers)
        gas_consumed.extend(r_gas_consumed)
        outputs.update(r_outputs)

        return index + j, transfers, outputs, gas_consumed

    @staticmethod
    def parallel_accumulation(
        work_reports: WorkReports,
        privileged_services: ChiZ,
        timeslot: Tau,
    ) -> Tuple[DeferredTransfers, BeefyMap, GasConsumed]:
        """
        Parallelized accumulation function ∆* defined in Eq 12.17
        Non-Sequential, Service-Aggregated Execution Pattern
        Transforms Initial Partial State, Sequence of Work Reports, and Dictionary of services (free, privileged accumulation)
        into Tuple of Total gas utilized in PVM, Posterior state-context, Resultant deferred-transfers and Accumulation-output pairings

        Args:
            partial_state (GhostPartial): The state context before accumulation, which includes service accounts and other mutable components.
            work_reports (WorkReports): A collection of work reports that are ready to be accumulated.
            privileged_services (ChiZ): A dictionary of services (by service index) that are set up for free accumulation along with their basic gas allowances.
            timeslot (Tau): Curr TimeSlot τ′

        Returns:
            A tuple (int, GhostPartial, DeferredTransfer, AccumulationOutput) where:
            Integer: Total gas utilized in PVM.
            GhostPartial: The updated state context after applying accumulation.
            DeferredTransfer: A list of transfers that are deferred.
            AccumulationOutput: A mapping of service indices to their corresponding accumulation outputs.
        """

        # All service IDs to accumulate
        # s in 12.17
        services: Set[ServiceId] = {
            digest.service_id
            for report in work_reports
            for digest in report.digests
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
        
        from jam.state.state import state

        for service in services:
            partial_state = state.to_partial()
            (
                partial_state,
                _transfers,
                _output_hash,
                _gas_consumed,
                _preimages,
            ) = Accumulation.single_accumulation(
                partial_state, work_reports, privileged_services, service, timeslot, state.eta[0]
            )
            gas_consumed.append((service, _gas_consumed))
            if _output_hash and _output_hash.unwrap() != Null:
                outputs.add((service, _output_hash.unwrap()))
            transfers.extend(_transfers)
            collected_preimages.update(_preimages)
            
            # Add partial cache to state
            state.store += partial_state.store

        Accumulation.preimage_integration(
            state.delta, collected_preimages, timeslot
        )
        return transfers, outputs, gas_consumed

    @staticmethod
    def single_accumulation(
        initial_state: GhostPartial,
        work_reports: WorkReports,
        services: ChiZ,
        service_id: ServiceId,
        timeslot: Tau,
        entropy: OpaqueHash
    ) -> AccumulationOutput:
        """
        Single-Service accumulation function ∆1 defined in Eq 12.19
        Transforms Initial Partial State, Sequence of Work Reports, Dictionary of services (free, privileged accumulation), and Service index
        into Tuple of Posterior state-context, Sequence of Transfers, Possible Accumulation-outputs and Actual gas utilized in PVM,

        Args:
            initial_state (GhostPartial): The state context before accumulation, which includes service accounts and other mutable components.
            work_reports (WorkReports): A collection of work reports that are ready to be accumulated.
            services (ChiZ): A dictionary of services (by service index) that are set up for free accumulation along with their basic gas allowances.
            service_id (ServiceId): Index of Particular Service
            timeslot (Tau): Curr TimeSlot τ′

        Returns:
            A tuple (GhostPartial, DeferredTransfer, AccOutput, Gas) where:
            GhostPartial: The updated state context after applying accumulation.
            DeferredTransfers: A list of transfers that are deferred.
            AccOutput: Possible accumulation outputs.
            Gas: Actual gas utilized in PVM.
        """

        g = Gas(0)
        i = OperandTuples([])

        if service_id in services:
            g = services[service_id]

        for w in work_reports:
            for r in w.digests:
                if r.service_id == service_id:
                    g += r.accumulate_gas
                    i.append(
                        OperandTuple(
                            p=w.package_spec.hash,
                            e=w.package_spec.exports_root,
                            a=w.authorizer_hash,
                            y=r.payload_hash,
                            g=Uint(r.accumulate_gas),
                            t=w.auth_output,
                            l=r.result,
                        )
                    )

        return PsiA(u=initial_state, t=timeslot, s=service_id, entropy=entropy, g=g, o=i).execute()

    @staticmethod
    def preimage_integration(
        accounts: Delta, preimages: Set[Tuple[ServiceId, Bytes]], timeslot: Tau
    ) -> Delta:
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
                raise ValueError(
                    "[Accumulation] Unexpected: Received preimage for a service that does not exist"
                )
            key_hash = Hash.blake2b(blobs)
            lookup = LookupTable(hash=key_hash,length= len(blobs))
            if len(service.lookup[lookup]) == 0:
                service.lookup[lookup] = Timestamps([timeslot])
                service.preimages[key_hash] = blobs

    @staticmethod
    def selection_fn(deferred_transfers: DeferredTransfers, service_id: ServiceId) -> DeferredTransfers:
        """
        Selection function X defined in Eq 12.29
        Maps a sequence of deferred transfers & a desired destination service index
        into sequence of transfers targeting said service

        Args:
            deferred_transfers (DeferredTransfers): Sequence of deferred transfers.
            service_id (ServiceId): Index of Particular Service

        Returns:
            DeferredTransfers: A list of ordered, deferred transfers.
        """

        service_transfers = DeferredTransfers([])
        for t in deferred_transfers:
            if t.receiver == service_id:
                service_transfers.append(t)
        return service_transfers

    @classmethod
    def transition(cls, pre_state: Sigma, state: Sigma, block: Block, newly_avail_wrs: WorkReports):
        """
        Transition the state's Delta, Xi, Omega, Chi, Iota, Phi components, calculate BEEFY Commitment Map.
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
            Update accumulation and ready queues, i.e., Xi, Omega state components
            Defined in eqn 12.25 - 12.27

        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/167d00167e00?v=0.7.0

        Args:
            state: State
            block: Block to import
            newly_avail_wrs: WRs that became newly available (from Reporting STF)

        Returns:
            State after transition
        """

        # ----------------------
        # Section 12.1: History & Queuing (Step 1 & 2)
        # ----------------------

        # Ready Queue
        omega = state.omega

        # Accumulated Queue
        xi_union = WorkDependencies([])

        for ep in state.xi:
            xi_union.extend(ep)

        # Latest Work Reports to Process
        work_reports = WorkReports(newly_avail_wrs)

        # Reports to be processed Immediately, Eq 12.4
        immediate_reports = cls.filter_wr_fn(work_reports)

        queued_wr = AllReadyWRs([])

        for wr in work_reports:
            if len(
                wr.context.prerequisites
            ) > 0 or len(wr.segment_root_lookup) > 0:
                rq = cls.fetch_dependencies(wr)
                queued_wr.append(rq)

        # Reports to be queued, Rq, Eq 12.5
        queued_reports = cls.queue_edit_fn(queued_wr, xi_union)

        # Calculate current timeslot index, Eq 12.10
        m = block.header.slot % EPOCH_LENGTH

        accumulatable_wr = AllReadyWRs([])

        q_right = omega[m:]
        q_left = omega[:m]

        for wrs in q_right:
            accumulatable_wr.extend(wrs)

        for wrs in q_left:
            accumulatable_wr.extend(wrs)

        accumulatable_wr.extend(queued_reports)

        # Calculate available wrs queue, q, Eq 12.12
        intermediate_queue = cls.queue_edit_fn(accumulatable_wr, cls.mapping_fn(immediate_reports))

        # Calculate accumulatable wrs queue, Q(q)
        accumulatable_wrs = cls.priority_queue_fn(intermediate_queue)

        # Evaluate ready to accumulate WRs, W! ⌢ Q(q), Eq 12.11
        star_work_reports = WorkReports([])
        star_work_reports.extend(immediate_reports)
        star_work_reports.extend(accumulatable_wrs)

        # ----------------------
        # Section 12.2 Execution (Step 3)
        # ----------------------

        # accumulation_gas for Chi_z_services (that automatically accumulates), Eqn 12.22
        service_gas=0
        for i in state.chi.chi_z:
            service_gas+=state.chi.chi_z[i]

        gas_limit = max(TOTAL_GAS,((ACCUMULATION_GAS*CORE_COUNT) + service_gas))

        [num_accumulated, deferred_transfers, commitment_map, gas_accumulations] = Accumulation.seq_accumulation(Gas(gas_limit), star_work_reports, state.chi.chi_z, block.header.slot)

        accumulation_stats = {}
        for ga in gas_accumulations:
            accumulation_stats[ga[0]] = [ga[1], 0]
        for i in range(num_accumulated):
            for d in star_work_reports[i].digests:
                accumulation_stats[d.service_id][1] += 1

        # Update Statistics
        pi = state.pi
        pi_service = pi.services
        for service_id in accumulation_stats.keys():
            if service_id not in pi_service:
                pi_service[service_id] = ServiceStat.empty()
            pi_service[service_id].accumulate_gas_used = Uint(accumulation_stats[service_id][0])
            pi_service[service_id].accumulate_count = Uint(accumulation_stats[service_id][1])
            state.delta[service_id].service.accumulated_at = block.header.slot
        pi.services = pi_service
        state.pi = pi

        # Update Chi, Iota, Phi, Theta
        theta = Theta([])
        for service_id, op in commitment_map:
            commitment = Commitment(service_id, op)
            theta.append(commitment)

        state.theta = theta
        

        # ----------------------
        # Section 12.3 Deferred Transfers & State Integration (Step 4)
        # ----------------------

        # fetch updated services
        services: List[ServiceId] = []
        for key in state.store._updates:
            exceptions = {0, 1,3,5,7}
            service_id = ServiceId.decode(bytes([key[1], key[3], key[5], key[7]]))
            if key[0] == 255 and service_id in state.delta:
                for i in range(31):
                    if i not in exceptions and key[i] != 0:
                        break
                else:
                    services.append(service_id)

        pi = state.pi
        for s in services:
            specific_transfers = Accumulation.selection_fn(deferred_transfers, s)
            # delta_double_dagger
            a, u = PsiT(d=state.delta, block_timeslot=block.header.slot, s=s, transfers=specific_transfers).execute()

            # Update Statistics
            if len(specific_transfers):
                pi_service = pi.services
                if s not in pi.services:
                    pi.services[s] = ServiceStat.empty()
                pi.services[s].on_transfers_count = Uint(len(specific_transfers))
                pi.services[s].on_transfers_gas_used = Uint(u)

                pi.services = pi_service

        state.pi = pi

        # Update Accumulated History, Xi
        xi = state.xi
        for i in range(EPOCH_LENGTH - 1):
            xi[i] = xi[i + 1]

        xi[EPOCH_LENGTH - 1] = cls.mapping_fn(star_work_reports)

        timeslot_difference = int(block.header.slot) - int(state.tau)

        # Update Ready Queue, Omega
        omega = state.omega
        for i in range(EPOCH_LENGTH):
            ind = (m + EPOCH_LENGTH - i) % EPOCH_LENGTH
            if i == 0:
                omega[ind] = cls.queue_edit_fn(
                    queued_reports, xi[EPOCH_LENGTH - 1]
                )
            elif 1 <= i < timeslot_difference:
                omega[ind] = AllReadyWRs([])
            elif i >= timeslot_difference:
                omega[ind] = cls.queue_edit_fn(
                    omega[ind], xi[EPOCH_LENGTH - 1]
                )
        state.xi = xi
        state.omega = omega

        from jam.settings import settings
        if settings.rpc_flag:
            keys = broker.topics.keys()
            matches = [k for k in keys if "subscribeServiceValue" in k]
            for req in matches:
                params = req.split(":")
                sid = ServiceId(params[1])
                key_list = json.loads(params[2])
                key = Bytes(key_list)
                finality = True if params[3] == 'True' else False
                value = state.delta[sid].storage.get(key) if state.delta[sid].storage.get(key) is None else list(state.delta[sid].storage.get(key))
                last_publish = broker.last_publish
                if req not in last_publish or last_publish[req] != value:
                    from jam.settings import settings
                    block = Finality.load_final(settings.main_db) if finality else Finality.load_latest(settings.main_db)

                    print(f"Req: {req} header_hash: {block.header.hash().hex()[:16]} slot: {block.header.slot} value: {value}")

                    asyncio.create_task(broker.publish(req,
                                                       {"header_hash": list(block.header.hash()),
                                                        "slot": int(block.header.slot), "value": value}))
                    broker.last_publish[req] = value

        return state, commitment_map