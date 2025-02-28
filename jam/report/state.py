from Cython.Compiler.Errors import message
from mesonbuild.dependencies.boost import boost_libraries

from jam.state.components.alpha import Alpha, AuthorizationPool
from jam.state.components.rho import WorkReportState
from jam.state.state import State
from jam.types import Block, decodable_choice, ServiceId, Boolean, Vector, AvailabilityAssignments, \
    AvailabilityAssignment, Null
import  dataclasses
from dataclasses import dataclass, replace
from jam.types.extrinsics.guarantees import GuaranteesExtrinsic

from jam.types.extrinsics import GuaranteesExtrinsic
from jam.types.work.report import WorkResults
from jam.utils.constants import ACCUMULATION_GAS, CORE_COUNT
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
    def transition(self, pre_state:State, block:Block)->State:
        new_state:State = dataclasses.replace(pre_state)

        Reporting.valid_report_fn()

        # State.rho
        # if new_state.rho[0] is not None:
        #     new_state.rho[0].report == workreport()
        # else:
        #     new_state.rho[0].time == slot


        Reporting.valid_report_fn (pre_state.alpha[0].AuthorizationPool)

        n = WorkReportState(generate_report(Block.extrinsic.guarantees),block.header.slot)
        generate_report(Block.extrinsic.guarantees)
        new_state.rho = n
        Reporting.result_fn(n.report.results,new_state)
        return new_state

    @staticmethod
    def valid_report_fn(auth_pool: AuthorizationPool,block:Block) -> Boolean:
        for x in block.extrinsic.guarantees:
            report_auth_hash = x.report.authorizer_hash
            core_index = x.report.core_index
            if report_auth_hash not in auth_pool[core_index]:
                raise ReportingError(
                    ReportingErrorCode.NOT_AUTHERIZED,
                    "Work Report's authorizer_hash not exist in AuthorizationPool"
                )

    @staticmethod
    def validator_index(avail_assignments:AvailabilityAssignments, block:Block):
        for x in block.extrinsic.guarantees:
            for y in x.signatures:
                if y.validator_index > VALIDATOR_COUNT:
                    raise ReportingError (
                        ReportingErrorCode.BAD_VALIDATOR_INDEX,
                        "validator index(signature) is out of range"
                    )

    @staticmethod
    def not_enough_guarantee(block:Block):
        for x in block.extrinsic.guarantees:
            credential_len = len(x.signatures)-1
            if credential_len <= 2:
                raise ReportingError (
                    ReportingErrorCode.NOT_ENOUGH_GUARANTEE,
                    "Work report don't have enough validator signature"
                )

    @staticmethod
    def not_sort_grnt_idx(block : Block):
        for x in block.extrinsic.guarantees:
            for y in x.signatures:
                if y.validator_index >= y.validator_index +1:
                    raise ReportingError (
                        ReportingErrorCode.NOT_SORTED_GUARANTOR,
                        "Work Report's Validator(make report valid or invalid) are not in sorted order in credential"
                    )

    @staticmethod
    def bad_core_index(block : Block):
        for x in block.extrinsic.guarantees:
            if x.report.core_index > CORE_COUNT:
                raise ReportingError (
                    ReportingErrorCode.BAD_CORE_INDEX,
                    "Core index value is more then CORE_COUNT"
                )


    @staticmethod
    def check_report_output(block : Block):
        for x in block.extrinsic.guarantees:
            output = x.report.auth_output


    @staticmethod
    def valid_signature():
        ...

    @decodable_choice
    def package_ava_fn(self, availabilitly:())->{}:
        ...


    @staticmethod
    def refinement_fn(state:State,block:Block):

        hashes = []

        for report in state.rho:
            hashes.append(report.report.package_spec.hash)


        for y in block.extrinsic.guarantees:
            context = y.report.context

            if context.anchor not in state.beta:
                return 'err'

            if not any(item["state_root"] == context.state_root for item in state.beta):
                return 'err'

            if context.lookup_anchor not in state.beta[:context.lookup_anchor_slot]:
                return 'err'

            if context.prerequisites is not None:
                for x in context.prerequisites:
                    if x not in hashes:
                        return 'err'







    def segement_root_lookup(self):
        ...

    @staticmethod
    def result_fn(results: WorkResults,state:State,):

        # for x in transition().rho:
        #     for y in x.report.results:
        #         if not y.accumulate_gas >= transition().delta[ServiceId].min_gas:
        #             return 'err'
        #         total_accumulate_gas = sum + y.accumulate_gas
        #     if not sum <= ACCUMULATION_GAS:
        #         return 'err'

        total_accumulate_gas = 0
        for x in results:

            # checking if code hash in results is avialable in state code hash or not
            if x.code_hash != State.delta[0].code_hash:
                return 'err'

            if x.service_id not in State.delta:
                return 'err'

            if x.accumulate_gas <= state.delta[0].min_gas:
                return 'err'

            total_accumulate_gas = total_accumulate_gas + x.accumulate_gas

        if total_accumulate_gas >= ACCUMULATION_GAS:
            return 'err'

        state.beta[0]

    @staticmethod
    def workreport_package( block:Block ) :
        hashes = []


        # storing package_spec hash of all reports in hashes
        for x in block.extrinsic.guarantees:
            hashes.append(x.report.package_spec.hash)


        for x in block.extrinsic.guarantees:
            if x.report.package_spec.hash in hashes:
                return 'err'






    @staticmethod
    def core_engaged(block:Block, state:State):
        for x in block.extrinsic.guarantees:
            if state.rho[x.report.core_index] is not Null:
                return 'err'


    @staticmethod
    def future_report(block:Block, state:State):
        for x in block.extrinsic.guarantees:
            if x.slot > block.header.slot:
                return 'err'








# test_instance = Rho
#     # Call the function and print the result
# result = test_instance.transition(State, Block )
# print(result)
