from copy import deepcopy
from typing import Tuple, Set, List, Dict, TYPE_CHECKING
from datetime import datetime

from tsrkit_types import U32
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import Uint
from tsrkit_types.null import Null

from jam.block import Block
from jam.execution.invocations.accumulate import PsiA
from jam.state.partial import GhostPartial
from jam.models.state.accumulation.types import (
    AccumulationOutput,
    DeferredTransfers,
    AccumulationInputs,
    OperandTuple,
    BeefyMap,
    GasConsumed, AccumulationInput,
)
from jam.models.protocol.crypto import Hash, OpaqueHash
from jam.models.state.pi import ServiceStat
from jam.models.state.sigma import Sigma
from jam.models.state.delta import Delta, LookupTable, Timestamps
from jam.models.state.tau import Tau
from jam.models.state.chi import ChiZ, Chi, ChiA
from jam.models.state.omega import AllReadyWRs, ReadyWR
from jam.models.state.theta import Commitment, Theta
from jam.models.protocol.core import Gas, ServiceId
from jam.models.work import (
    WorkDependencies,
    WorkReports,
    WorkReport,
)
from jam.utils.constants import EPOCH_LENGTH, TOTAL_GAS, ACCUMULATION_GAS, CORE_COUNT

if TYPE_CHECKING:
    from jam.state.state import State

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
        deferred_transfers: DeferredTransfers,
        work_reports: WorkReports,
        state: Sigma,
        privileged_services: ChiZ
    ) -> Tuple[int, BeefyMap, GasConsumed, DeferredTransfers]:
        """
        Outer accumulation function ∆+ defined in Eq 12.18
        Sequential Execution Pattern
        Transforms Gas Limit, Sequence of Deferred Transfers, Sequence of Work Reports, Initial Partial State and Dictionary of services (free, privileged accumulation)
        into Tuple of No. of Work results accumulated, Accumulation-output pairings, Gas utilized per service in PVM

        Args:
            gas_limit (Gas): The total gas available for the accumulation process.
            work_reports (WorkReports): A collection of work reports that are ready to be accumulated.
            deferred_transfers (DeferredTransfers): A sequence of deferred transfers.
            state (State): Posterior State for building initial partial state.
            privileged_services (ChiZ): Set of services enjoying free accumulation.

        Returns:
            A tuple (int, BeefyMap, GasConsumed, Deferred Transfers) where:
            Integer: Number of work digests successfully accumulated.
            BeefyMap: A mapping of service indices to their corresponding accumulation outputs.
            GasConsumed: Gas consumed by accumulation of each service along with their service id
            DeferredTransfers: Processed Transfers Count
        Note:
            PartialState is not returned as all the changes are available in global state itself.
        """

        index = 0
        report_gas = 0
        for i in work_reports:
            for j in i.digests:
                report_gas += j.accumulate_gas
            if report_gas > gas_limit:
                break
            index = index + 1

        n = len(deferred_transfers) + index + len(privileged_services)

        if n == 0:
            return 0, set(), [], DeferredTransfers([])

        work_reports_start = work_reports[: index]
        # Parallely accumulate ChiZ services (always accumulate services)
        transfers, outputs, gas_consumed = Accumulation.parallel_accumulation(
            state, deferred_transfers, work_reports_start, privileged_services
        )

        gas_star = gas_limit
        for t in deferred_transfers:
            gas_star += t.gas

        work_reports_end = work_reports[index:]

        utilized_gas = Gas(0)
        for _, gas in gas_consumed:
            utilized_gas += gas

        gas_diff = gas_star - utilized_gas

        j, r_outputs, r_gas_consumed, transfers_tail = (
            Accumulation.seq_accumulation(
                gas_diff, transfers, work_reports_end, state, ChiZ({})
            )
        )

        gas_consumed.extend(r_gas_consumed)
        outputs.update(r_outputs)
        processed_transfers = DeferredTransfers(list(deferred_transfers))
        processed_transfers.extend(transfers_tail)

        return index + j, outputs, gas_consumed, processed_transfers

    @staticmethod
    def parallel_accumulation(
        state: "State",
        deferred_transfers: DeferredTransfers,
        work_reports: WorkReports,
        privileged_services: ChiZ
    ) -> Tuple[DeferredTransfers, BeefyMap, GasConsumed]:
        """
        Parallelized accumulation function ∆* defined in Eq 12.19
        Non-Sequential, Service-Aggregated Execution Pattern
        Transforms Initial Partial State, Sequence of Deferred transfers, Sequence of Work Reports,
        and Dictionary of services (free, privileged accumulation)
        into Tuple of Resultant deferred-transfers and Accumulation-output pairings, Gas utilized per service in PVM.

        Args:
            state (State): Posterior State.
            deferred_transfers (DeferredTransfers): A sequence of Deferred transfers.
            work_reports (WorkReports): A collection of work reports that are ready to be accumulated.
            privileged_services (ChiZ): Set of services enjoying free accumulation

        Returns:
            A tuple (DeferredTransfers, BeefyMap, GasConsumed) where:
            DeferredTransfers: A list of transfers that are deferred.
            BeefyMap: A mapping of service indices to their corresponding accumulation outputs.
            GasConsumed: Gas consumed by accumulation of each service along with their service id

        Note:
            PartialState is not returned as all the changes are available in global state itself.
        """

        partial_state = state.to_partial()
        e = partial_state.clone(True)

        timeslot = state.tau

        # All service IDs to accumulate
        # s in 12.19
        services: Set[ServiceId] = {
            digest.service_id
            for report in work_reports
            for digest in report.digests
        }

        services.update(privileged_services.keys())
        for t in deferred_transfers:
            services.add(t.receiver)

        ordered_services = sorted(services, key=int)

        # Accumulated gas by each service
        # u in 12.19
        gas_consumed: GasConsumed = []

        # Accumulation output hashes
        # b in 12.19
        outputs: BeefyMap = set()

        # Deferred transfers
        # t_telda in 12.19
        transfers = DeferredTransfers([])

        collected_preimages: Set[Tuple[ServiceId, Bytes]] = set()

        # accumulation cache
        acc_map: Dict[ServiceId, GhostPartial] = {}

        # --------------------------------------
        # Accumulation of reported services (W) &
        # always accumulate services (CHI_Z)
        # --------------------------------------
        for service in ordered_services:
            (
                partial_state,
                _transfers,
                _output_hash,
                _gas_consumed,
                _preimages,
            ) = Accumulation.single_accumulation(
                e, deferred_transfers, work_reports, privileged_services, service, timeslot, state.eta[0]
            )
            acc_map[service] = partial_state
            gas_consumed.append((service, _gas_consumed))

            if _output_hash and _output_hash.unwrap() != Null:
                outputs.add((service, _output_hash.unwrap()))
            transfers.extend(_transfers)
            collected_preimages.update(_preimages)

            # Add partial cache to state
            state.store += partial_state.store
        # --------------------------------------


        # --------------------------------------
        # Preimages Integration
        # --------------------------------------
        Accumulation.preimage_integration(
            state.delta, collected_preimages, timeslot
        )


        # q
        prior_phi = e.authorizer_keys

        # m
        prior_chi_m = e.privileges.chi_m

        # a
        prior_chi_a = e.privileges.chi_a

        # v
        prior_chi_v = e.privileges.chi_v

        # r
        prior_chi_r = e.privileges.chi_r
        # --------------------------------------


        # --------------------------------------
        # Accumulation of privileged services
        # (CHI_M, CHI_A, CHI_V, CHI_R)
        # --------------------------------------

        # 1. chi_m -> m', a*, v*, r*, z'
        if prior_chi_m not in acc_map:
            partial_state, _, _, _, _ = Accumulation.single_accumulation(
                e, deferred_transfers, work_reports, privileged_services, prior_chi_m, timeslot, state.eta[0]
            )
            acc_map[prior_chi_m] = partial_state
        else:
            partial_state = acc_map[prior_chi_m]

        # e*
        e_star = partial_state.clone(True)

        # m'
        posterior_chi_m = e_star.privileges.chi_m

        # a*
        chi_a_star = e_star.privileges.chi_a

        # v*
        chi_v_star = e_star.privileges.chi_v

        # r*
        chi_r_star = e_star.privileges.chi_r

        # z'
        posterior_chi_z = e_star.privileges.chi_z


        # 2. chi_a_star -> a'

        # a'
        posterior_chi_a = prior_chi_a

        for c_index in range(CORE_COUNT):
            if chi_a_star[c_index] == prior_chi_a[c_index]:
                if chi_a_star[c_index] not in acc_map:
                    partial_state, _, _, _, _ = Accumulation.single_accumulation(
                        e, deferred_transfers, work_reports, privileged_services, chi_a_star[c_index], timeslot, state.eta[0]
                    )
                    acc_map[chi_a_star[c_index]] = partial_state
                else:
                    partial_state = acc_map[chi_a_star[c_index]]
            else:
                partial_state = e_star

            posterior_chi_a[c_index] = partial_state.privileges.chi_a[c_index]

        # 3. chi_v_star -> v'
        if chi_v_star == prior_chi_v:
            if chi_v_star not in acc_map:
                partial_state, _, _, _, _ = Accumulation.single_accumulation(
                    e, deferred_transfers, work_reports, privileged_services, chi_v_star, timeslot, state.eta[0]
                )
                acc_map[chi_v_star] = partial_state
            else:
                partial_state = acc_map[chi_v_star]
        else:
            partial_state = e_star

        # v'
        posterior_chi_v = partial_state.privileges.chi_v

        # 4. chi_r* -> r'
        if chi_r_star == prior_chi_r:
            if chi_r_star not in acc_map:
                partial_state, _, _, _, _ = Accumulation.single_accumulation(
                    e, deferred_transfers, work_reports, privileged_services, chi_r_star, timeslot, state.eta[0]
                )
                acc_map[chi_r_star] = partial_state
            else:
                partial_state = acc_map[chi_r_star]
        else:
            partial_state = e_star

        # r'
        posterior_chi_r = partial_state.privileges.chi_r

        # 5. chi_v -> i'
        if prior_chi_v not in acc_map:
            partial_state, _, _, _, _ = Accumulation.single_accumulation(
                e, deferred_transfers, work_reports, privileged_services, prior_chi_v, timeslot, state.eta[0]
            )
            acc_map[prior_chi_v] = partial_state
        else:
            partial_state = acc_map[prior_chi_v]


        # i'
        posterior_iota = partial_state.validator_keys

        # 6. chi_a -> q'

        # q'
        posterior_phi = prior_phi

        for c_index in range(CORE_COUNT):
            if prior_chi_a[c_index] not in acc_map:
                partial_state, _, _, _, _ = Accumulation.single_accumulation(
                    e, deferred_transfers, work_reports, privileged_services, prior_chi_a[c_index], timeslot, state.eta[0]
                )
                acc_map[prior_chi_a[c_index]] = partial_state
            else:
                partial_state = acc_map[prior_chi_a[c_index]]

            posterior_phi[c_index] = partial_state.authorizer_keys[c_index]

        # --------------------------------------

        state.phi = posterior_phi
        state.iota = posterior_iota
        state.chi = Chi(chi_m=posterior_chi_m, chi_a=posterior_chi_a, chi_v=posterior_chi_v, chi_r=posterior_chi_r, chi_z=posterior_chi_z)


        return transfers, outputs, gas_consumed

    @staticmethod
    def single_accumulation(
        initial_state: GhostPartial,
        deferred_transfers: DeferredTransfers,
        work_reports: WorkReports,
        services: ChiZ,
        service_id: ServiceId,
        timeslot: Tau,
        entropy: OpaqueHash
    ) -> AccumulationOutput:
        """
        Single-Service accumulation function ∆1 defined in Eq 12.24
        Transforms Initial Partial State, Sequence of Work Reports,
        dictionary of services (free, privileged accumulation), and Service index
        into Tuple of Posterior state-context, Sequence of Transfers, Possible Accumulation-outputs
        and Actual gas utilized in PVM,

        Args:
            deferred_transfers:
            initial_state (GhostPartial): The state context before accumulation, which includes service accounts and other mutable components.
            work_reports (WorkReports): A collection of work reports that are ready to be accumulated.
            services (ChiZ): A dictionary of services (by service index) that are set up for free accumulation along with their basic gas allowances.
            service_id (ServiceId): Index of Particular Service
            timeslot (Tau): Curr TimeSlot τ′
            entropy (Eta[0]): Entropy Source

        Returns:
            A tuple (GhostPartial, DeferredTransfer, AccOutput, Gas) where:
            GhostPartial: The updated state context after applying accumulation.
            DeferredTransfers: A list of transfers that are deferred.
            AccOutput: Possible accumulation o
        """

        g = Gas(0)
        i = AccumulationInputs([])

        if service_id in services:
            g = services[service_id]

        for t in deferred_transfers:
            if t.receiver == service_id:
                g += t.gas
                i.append(AccumulationInput(t))

        for w in work_reports:
            for r in w.digests:
                if r.service_id == service_id:
                    g += r.accumulate_gas
                    i.append(
                        AccumulationInput(
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
                    )

        if initial_state.service_accounts[service_id] is None:
            return initial_state, DeferredTransfers([]), None, Gas(0), set()

        return PsiA(u=initial_state, t=timeslot, s=service_id, entropy=entropy, g=g, i=i).execute()

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
            lookup = LookupTable(hash=key_hash,length=U32(len(blobs)))
            if service.lookup[lookup] is not None and len(service.lookup[lookup]) == 0:
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

        deferred_transfers: DeferredTransfers = DeferredTransfers([])
        [num_accumulated, commitment_map, gas_accumulations, processed_transfers] = Accumulation.seq_accumulation(Gas(gas_limit), deferred_transfers, star_work_reports, state, state.chi.chi_z)

        # S: service_id -> [acc_count, transfers_count, gas_used]
        # S(s) = (N(s), T(s), G(s)):
        accumulation_stats = {}
        for i in range(num_accumulated):
            for d in star_work_reports[i].digests:
                if d.service_id not in accumulation_stats:
                    accumulation_stats[d.service_id] = [0, 0, 0]
                accumulation_stats[d.service_id][0] += 1

        for transfer in processed_transfers:
            if transfer.receiver not in accumulation_stats:
                accumulation_stats[transfer.receiver] = [0, 0, 0]
            accumulation_stats[transfer.receiver][1] += 1

        for service_id, gas in gas_accumulations:
            if service_id not in accumulation_stats:
                accumulation_stats[service_id] = [0, 0, 0]
            accumulation_stats[service_id][2] += gas

        # Update Statistics
        pi = state.pi
        pi_service = pi.services
        for service_id, stats in accumulation_stats.items():
            if stats == [0, 0, 0]:
                continue

            if service_id not in pi_service:
                pi_service[service_id] = ServiceStat.empty()
            pi_service[service_id].accumulate_count = Uint(stats[0])
            pi_service[service_id].transfers_count = Uint(stats[1])
            pi_service[service_id].accumulate_gas_used = Uint(stats[2])

            account = state.delta[service_id]
            if account is not None:
                account.service.accumulated_at = block.header.slot
        pi.services = pi_service
        state.pi = pi

        # Update Chi, Iota, Phi, Theta
        theta = Theta([])
        for service_id, op in commitment_map:
            commitment = Commitment(service_id, op)
            theta.append(commitment)

        def sort_fn(comm: Commitment):
            return (
                int(comm.service_id),
                comm.output,
            )

        state.theta = Theta(sorted(theta, key=sort_fn))

        # ----------------------
        # Section 12.3 Final State Integration (Step 4)
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
        
        # Cleanup removed services from Pi
        pi_services_to_remove = []
        for s_id in pi.services.keys():
            if s_id not in state.delta:
                pi_services_to_remove.append(s_id)
        
        for s_id in pi_services_to_remove:
            del pi.services[s_id]

        state.pi = pi

        # Update Accumulated History, Xi
        xi = state.xi
        for i in range(EPOCH_LENGTH - 1):
            xi[i] = xi[i + 1]

        xi[EPOCH_LENGTH - 1] = cls.mapping_fn(star_work_reports)

        timeslot_difference = int(state.tau) - int(pre_state.tau)

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

        return state, commitment_map
