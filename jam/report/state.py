from jam.report.check import auth_pool
from jam.state.components.alpha import Alpha, AuthorizationPool
from jam.state.components.rho import WorkReportState, OptionalWorkReportState
from jam.state.state import State
from jam.types import Block, decodable_choice, ServiceId, Boolean, Vector, AvailabilityAssignments, \
    AvailabilityAssignment, Null, String, U64, U16, Bytes
import  dataclasses
from dataclasses import dataclass, replace
from jam.types.extrinsics.guarantees import GuaranteesExtrinsic

from jam.types.extrinsics import GuaranteesExtrinsic
from jam.types.work.report import WorkResults
from jam.utils.constants import ACCUMULATION_GAS, CORE_COUNT, MAX_DEPENDENCIES
from jam.report.error import ReportingError, ReportingErrorCode
from jam.types.protocol.availability import AvailabilityAssignments
from jam.utils.constants import CORE_COUNT
from jam.utils.constants import VALIDATOR_COUNT

def generate_report(report : GuaranteesExtrinsic)->GuaranteesExtrinsic:
    guarantees: GuaranteesExtrinsic=Vector(GuaranteesExtrinsic)
    # for x in report:
    #     WorkReport.time = x.slot
    #     WorkReport.report = x.report
    for guarantee in guarantees:
        guarantee.report.package_spec.hash= report[0].report.package_spec.hash
        guarantee.report.package_spec.length = report[0].report.package_spec.length
        guarantee.report.package_spec.erasure_root = report[0].report.package_spec.erasure_root
        guarantee.report.package_spec.exports_root = report[0].report.package_spec.exports_root
        guarantee.report.package_spec.exports_count = report[0].report.package_spec.exports_count

        guarantee.report.context.anchor = report[0].report.context.anchor
        guarantee.report.context.state_root = report[0].report.context.state_root
        guarantee.report.context.beefy_root = report[0].report.context.beefy_root
        guarantee.report.context.lookup_anchor = report[0].report.context.lookup_anchor
        guarantee.report.context.lookup_anchor_slot = report[0].report.context.lookup_anchor_slot
        guarantee.report.context.lookup_anchor_slot = report[0].report.context.lookup_anchor_slot
        guarantee.report.core_index = report[0].report.core_index
        guarantee.report.authorizer_hash = report[0].report.authorizer_hash
        guarantee.report.auth_output = report[0].report.auth_output
        guarantee.report.segment_root_lookup = report[0].report.segment_root_lookup

        for x, y in zip(guarantee.report.results, report[0].report.results):
            x.service_id = y.service_id
            x.code_hash = y.code_hash
            x.payload_hash = y.payload_hash
            x.accumulate_gas = y.accumulate_gas
            x.result = y.resultWorkReport.report.results,report[0].report.results

        guarantee.slot = report[0].slot

        for x, y in zip(guarantee.signatures, report[0].signatures):
            x.validator_index = y.validator_index
            x.signature = y.signature




    return guarantees



class Reporting:

    @staticmethod
    def transition(pre_state:State, block:Block)->State:
        new_state:State = dataclasses.replace(pre_state)
        header_hashes = []

        # for x in new_state.beta:
        #     header_hashes.append(x.header_hash)
        #
        # results = block.extrinsic.guarantees
        #
        #
        #
        # for x in block.extrinsic.guarantees:
        #     context = x.report.context
        #     # print('hhhhhh', context.anchor, new_state.beta)
        #     if context.anchor not in header_hashes:
        #         print(U64(x.report.core_index))
        #         raise ReportingError(
        #             ReportingErrorCode.ANCHOR_NOT_RECENT,
        #             "Anchor not present in recent blocks hash"
        #         )
            # if context.beefy_root not in pre_state.rho:
            #     print('hhhh1')
            #     raise ReportingError(
            #         ReportingErrorCode.BAD_BEEFY_MMR_ROOT
            #     )

        # print('hhh')



        # for x in results:
        #     for y in x.report.results:
        #         print('hehe')
        #         if y.code_hash != pre_state.delta[y.service_id].code_hash:
        #             print(y.code_hash)
        #             print(pre_state.delta[y.service_id].code_hash)
        #             print(y.code_hash == pre_state.delta[y.service_id].code_hash)
        #             raise ReportingError(
        #                 ReportingErrorCode.BAD_CODE_HASH
        #             )

        Reporting.refinement_fn(pre_state,block)
        Reporting.bad_core_index(block)
        Reporting.result_fn(pre_state,block)
        Reporting.validator_index(block)
        # Reporting.core_engaged(pre_state,block)
        Reporting.duplicate_pkg_recent_history(pre_state,block)

        Reporting.future_report(block)
        Reporting.not_enough_guarantee(block)
        Reporting.valid_report_fn(pre_state,block)
        Reporting.not_sort_grnt_idx(block)
        Reporting.duplicate_pkg_report(pre_state, block)
        Reporting.guarantee_order(block)
        Reporting.check_multiple_reports(pre_state,block)
        Reporting.check_multiple_dependencies(pre_state,block)
        Reporting.big_work_report_output(pre_state, block)
        Reporting.check_dependencies(block)


        # Reporting.refinement_fn(pre_state,block)
        # Reporting.result_fn(pre_state, block)
        # Reporting.valid_report_fn()

        # Reporting.result_fn(pre_state, block)
        # Reporting.duplicate_pkg_recent_history(pre_state, block)
        # State.rho
        # if new_state.rho[0] is not None:
        #     new_state.rho[0].report == workreport()
        # else:
        #     new_state.rho[0].time == slot


        # Reporting.valid_report_fn (pre_state, block)
        #
        # n = WorkReportState(generate_report(block.extrinsic.guarantees),block.header.slot)
        # generate_report(Block.extrinsic.guarantees)
        # new_state.rho = n
        # Reporting.result_fn(n.report.results,new_state)
        return new_state


    @staticmethod
    def check_dependencies(block : Block):
        for x in block.extrinsic.guarantees:
            segment_depd = len(x.report.segment_root_lookup)
            prerequisite = len(x.report.context.prerequisites)
            if (segment_depd + prerequisite) > MAX_DEPENDENCIES:
                raise ReportingError (
                    ReportingErrorCode.TOO_MANY_DEPENDENCIES,
                    "Work package has too many dependencies(segment_lookup + prerequisite) "
                )



    @staticmethod
    def guarantee_order(block :Block):
        for i in range(len(block.extrinsic.guarantees)-1):  # added -1 as index was getting out of range for some test cases
            if block.extrinsic.guarantees[i].report.core_index == block.extrinsic.guarantees[i+1].report.core_index:
                raise ReportingError (
                    ReportingErrorCode.OUT_OF_ORDER_GUARANTEE,
                    "Core index for each guarantee is not in unique"
                )

    @staticmethod
    def not_sort_grnt_idx(block: Block):
        for i in block.extrinsic.guarantees:
            for j in range(len(i.signatures)-1):
                if i.signatures[j].validator_index >= i.signatures[j+1].validator_index:
                    raise ReportingError (
                        ReportingErrorCode.NOT_SORTED_OR_UNIQUE_GUARANTORS,
                        "Signature's validator index order is not sorted"
                    )

    @staticmethod
    def valid_report_fn(state: State,block:Block):
        auth_pool = state.alpha
        for x in block.extrinsic.guarantees:
            report_auth_hash = x.report.authorizer_hash
            core_index = x.report.core_index
            if report_auth_hash not in auth_pool[core_index]:
                raise ReportingError(
                    ReportingErrorCode.CORE_UNAUTHORIZED,
                    "Work Report's authorizer_hash not exist in AuthorizationPool"
                )

    @staticmethod
    def validator_index( block:Block):
        for x in block.extrinsic.guarantees:
            for y in x.signatures:
                if y.validator_index >= VALIDATOR_COUNT:
                    raise ReportingError (
                        ReportingErrorCode.BAD_VALIDATOR_INDEX,
                        "validator index(signature) is out of range"
                    )

    @staticmethod
    def not_enough_guarantee(block:Block):
        for x in block.extrinsic.guarantees:
            credential_len = len(x.signatures)   #removed -1
            print('credential length',credential_len)
            if credential_len < 2:
                raise ReportingError (
                    ReportingErrorCode.INSUFFICIENT_GURANTEE,
                    "Work report don't have enough validator signature"
                )

    @staticmethod
    def bad_core_index(block : Block):
        for x in block.extrinsic.guarantees:
            print('coreindex')
            if x.report.core_index > CORE_COUNT:
                raise ReportingError (
                    ReportingErrorCode.BAD_CORE_INDEX,
                    "Core index value is more then CORE_COUNT"
                )

    @staticmethod
    def duplicate_pkg_recent_history(state: State,block : Block):
        hashes = []
        for x in block.extrinsic.guarantees:
            hashes.append(x.report.package_spec.hash)

        for i in state.beta:
                print('in duplicate package')
                print('packages',hashes[0],i.packages)
                # if i.packages in hashes:
                if any(key in hashes for key in i.packages.keys()):
                    print('inside recent history')
                    raise ReportingError (
                        ReportingErrorCode.DUPLICATE_PACKAGE,
                        "Work package is already executed in recent-block's history"
                    )


    @staticmethod
    def duplicate_pkg_report(state: State , block :Block):
        print('ddduppp')
        if len(block.extrinsic.guarantees)>1:
            for x in range (len(block.extrinsic.guarantees)):
                print('dduuppp1',x,len(block.extrinsic.guarantees))
                for y in range(x+1, len(block.extrinsic.guarantees)): # removed -1 as it was causing error index out of range
                    print('x=',x,'y=',y,'length of gurant',len(block.extrinsic.guarantees))
                    # print('in duplicate package',block.extrinsic.guarantees[x].report.package_spec.hash,block.extrinsic.guarantees[y].report.package_spec.hash)
                    if block.extrinsic.guarantees[x].report.package_spec.hash == block.extrinsic.guarantees[y].report.package_spec.hash:
                        raise ReportingError(
                            ReportingErrorCode.DUPLICATE_PACKAGE
                        )


    @staticmethod
    def refinement_fn(state:State,block:Block):

        work_package_hashes = []

        for x in state.beta:
            for key in x.packages:
                work_package_hashes.append(key)

        hashes = []
        #
        for report in block.extrinsic.guarantees:
        #     report.
            hashes.append(report.report.package_spec.hash)

        header_hashes = []

        for x in state.beta:
            header_hashes.append(x.header_hash)

        print(header_hashes)
        for y in block.extrinsic.guarantees:
            context = y.report.context

            if context.anchor not in header_hashes:
                print(context.anchor)
                raise ReportingError(
                    ReportingErrorCode.ANCHOR_NOT_RECENT
                )


            if not any(item.state_root == context.state_root for item in state.beta):
                raise ReportingError(
                    ReportingErrorCode.BAD_STATE_ROOT
                )

            # else:
            #     raise ReportingError(
            #         ReportingErrorCode.BAD_BEEFY_MMR_ROOT
            #     )

            # if context.lookup_anchor not in state.beta[:context.lookup_anchor_slot]:
            #     return 'err'



            # In this we are checking if prerequisites array is not null , then
            # its hashes must match with package spec hash of previous reports
            if context.prerequisites != Null : # changed from is not None to != Null
                # print(context.prerequisites != Null)
                 for x in context.prerequisites:
                    print('x = ',x,'work package',work_package_hashes,'hashes ',hashes)
                    if x not in  hashes and x not in work_package_hashes:
                        raise ReportingError(
                            ReportingErrorCode.DEPENDENCY_MISSING
                        )
            print('segment')
            if  y.report.segment_root_lookup != Null:
                for x in y.report.segment_root_lookup:
                    if x.work_package_hash not in hashes and x.work_package_hash not in work_package_hashes:
                        raise ReportingError(
                            ReportingErrorCode.DEPENDENCY_MISSING
                        )

    def segement_root_lookup(self):
        ...

    @staticmethod
    def result_fn(state:State,block:Block):

        results = block.extrinsic.guarantees
        total_accumulate_gas = 0
        for x in results:

            for y in x.report.results:
                if y.service_id not in state.delta:
                    print("service")
                    raise ReportingError(
                        ReportingErrorCode.BAD_SERVICE_ID
                    )
                print('in code hash')
                if y.code_hash != state.delta[y.service_id].code_hash:
                    raise ReportingError(
                        ReportingErrorCode.BAD_CODE_HASH
                    )
                print('outside service id')

                if y.accumulate_gas < state.delta[y.service_id].min_gas:
                    raise ReportingError(
                        ReportingErrorCode.SERVICE_ITEM_GAS_TOO_LOW
                    )

                total_accumulate_gas = total_accumulate_gas + y.accumulate_gas




        if total_accumulate_gas > ACCUMULATION_GAS:
            # print('in high work report gas',total_accumulate_gas)
            for core in range(len(block.extrinsic.guarantees)):
                # print('core value',core)
                    # print(state.rho.)
                state.rho[core] = OptionalWorkReportState(
                    WorkReportState(
                        report=block.extrinsic.guarantees[core].report,
                        timeout=block.extrinsic.guarantees[core].slot
                        )
                    )
                # print(core,'---> ',state.rho[core])
                # print(core,'--->',block.extrinsic.guarantees[core].report)
        return state

        # for x in transition().rho:
        #     for y in x.report.results:
        #         if not y.accumulate_gas >= transition().delta[ServiceId].min_gas:
        #             return 'err'
        #         total_accumulate_gas = sum + y.accumulate_gas
        #     if not sum <= ACCUMULATION_GAS:
        #         return 'err'

        #
        # for x in results:
        #
        #     # checking if code hash in results is available in state code hash or not
        #     if x.code_hash != state.delta[0].code_hash:
        #         return 'err'


        #
        #     if x.accumulate_gas <= state.delta[0].min_gas:
        #         return 'err'
        #
        #     total_accumulate_gas = total_accumulate_gas + x.accumulate_gas
        #
        # if total_accumulate_gas >= ACCUMULATION_GAS:
        #     return 'err'
        #
        # state.beta[0]

    @staticmethod
    def workreport_package( block:Block ) :
        hashes = []

        # storing package_spec hash of all reports in hashes
        for x in block.extrinsic.guarantees:
            if x.report.package_spec.hash not in hashes:
                hashes.append(x.report.package_spec.hash)
            else :
                raise ReportingError(
                    ReportingErrorCode.DUPLICATE_PACKAGE_IN_REPORT,
                    "Two work reports of the same package(no duplicate work-package hash)"
                )

        # @staticmethod
        # def ensure_assurances_unique(assurances: List[AvailAssurance]) -> None:
        #     """Ensure the assurances are unique using Python's set"""
        #     if len(assurances) != len(set(assurance.validator_index for assurance in assurances)):
        #         raise AssurancesError(AssurancesErrorCode.NOT_SORTED_OR_UNIQUE_ASSURERS,
        #                               "Assurances are not unique by validator index")



        for x in block.extrinsic.guarantees:
            if x.report.package_spec.hash in hashes:
                return 'err'

    @staticmethod
    def core_engaged(state:State,block:Block):
        for x in block.extrinsic.guarantees:
            print(x.report.core_index,state.rho[x.report.core_index] == Null)
            if state.rho[x.report.core_index] != Null:
                raise ReportingError(
                    ReportingErrorCode.CORE_ENGAGED
                )

    @staticmethod
    def future_report(block:Block):
        for x in block.extrinsic.guarantees:
            if x.slot > block.header.slot:
                raise ReportingError(
                    ReportingErrorCode.FUTURE_REPORT_SLOT
                )

    @staticmethod
    def high_work_report_gas(state:State, block:Block):
        total_gas =0
        service_id = 0
        for x in block.extrinsic.guarantees:
            for y in x.report.results:
                service_id = y.service_id
                total_gas = total_gas + y.accumulate_gas
        if state.delta[service_id].balance < total_gas:

          print('gas limit ')

    #     for x in state.delta:

    @staticmethod
    def check_multiple_reports(state:State, block:Block):
        if len(block.extrinsic.guarantees) >1:
            for core in range(len(block.extrinsic.guarantees)):
                # print('core value',core)
                    # print(state.rho.)
                state.rho[core] = OptionalWorkReportState(
                    WorkReportState(
                        report=block.extrinsic.guarantees[core].report,
                        timeout=block.extrinsic.guarantees[core].slot
                        )
                    )
            return state

    @staticmethod
    def check_multiple_dependencies(state:State, block:Block):
        for x in block.extrinsic.guarantees:
            if len(x.report.context.prerequisites)> 0 and len(x.report.segment_root_lookup)>0:
                for core in range(len(block.extrinsic.guarantees)):
                        # print('core value',core)
                        # print(state.rho.)
                    state.rho[core] = OptionalWorkReportState(
                            WorkReportState(
                                report=block.extrinsic.guarantees[core].report,
                                timeout=block.extrinsic.guarantees[core].slot
                            )
                        )
        return state


    @staticmethod
    def big_work_report_output(state:State, block:Block):
        work_report_output = Bytes(0)

        for x in block.extrinsic.guarantees:

            work_report_output = work_report_output + x.report.auth_output

            for y in x.report.results:
                # print('result value',y.result.get_value())
                work_report_output = work_report_output + y.result.get_value()
        # print(work_report_output < Bytes(48 * (2 ** 10)))
        if work_report_output < Bytes(48 * (2 ** 10)):
            for core in range(len(block.extrinsic.guarantees)):
                # print('core value',core)
                # print(state.rho.)
                state.rho[core] = OptionalWorkReportState(
                    WorkReportState(
                        report=block.extrinsic.guarantees[core].report,
                        timeout=block.extrinsic.guarantees[core].slot
                    )
                )
        return state
        # print('total output',work_report_output)



