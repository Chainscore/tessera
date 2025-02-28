from Cython.Compiler.Errors import message
from mesonbuild.dependencies.boost import boost_libraries

from jam.state.components.alpha import Alpha, AuthorizationPool
from jam.state.components.rho import WorkReportState
from jam.state.state import State
from jam.types import Block, decodable_choice, ServiceId, Boolean
import  dataclasses
from dataclasses import dataclass, replace
from jam.types.extrinsics.guarantees import GuaranteesExtrinsic

from jam.types.extrinsics import GuaranteesExtrinsic
from jam.utils.constants import ACCUMULATION_GAS, CORE_COUNT
from jam.report.error import ReportingError, ReportingErrorCode
from jam.types.protocol.availability import AvailabilityAssignments
from jam.utils.constants import CORE_COUNT
from jam.utils.constants import VALIDATOR_COUNT

def generate_report(report : GuaranteesExtrinsic)->WorkReportState.report:
    Guarantee: GuaranteesExtrinsic
    # for x in report:
    #     WorkReport.time = x.slot
    #     WorkReport.report = x.report

    Guarantee[0].report.package_spec.hash= report[0].report.package_spec.hash
    Guarantee[0].report.package_spec.length = report[0].report.package_spec.length
    Guarantee[0].report.package_spec.erasure_root = report[0].report.package_spec.erasure_root
    Guarantee[0].report.package_spec.exports_root = report[0].report.package_spec.exports_root
    Guarantee[0].report.package_spec.exports_count = report[0].report.package_spec.exports_count

    Guarantee[0].report.context.anchor = report[0].report.context.anchor
    Guarantee[0].report.context.state_root = report[0].report.context.state_root
    Guarantee[0].report.context.beefy_root = report[0].report.context.beefy_root
    Guarantee[0].report.context.lookup_anchor = report[0].report.context.lookup_anchor
    Guarantee[0].report.context.lookup_anchor_slot = report[0].report.context.lookup_anchor_slot
    Guarantee[0].report.context.lookup_anchor_slot = report[0].report.context.lookup_anchor_slot
    Guarantee[0].report.core_index = report[0].report.core_index
    Guarantee[0].report.authorizer_hash = report[0].report.authorizer_hash
    Guarantee[0].report.auth_output = report[0].report.auth_output
    Guarantee[0].report.segment_root_lookup = report[0].report.segment_root_lookup

    for x, y in zip(Guarantee[0].report.results, report[0].report.results):
        x.service_id = y.service_id
        x.code_hash = y.code_hash
        x.payload_hash = y.payload_hash
        x.accumulate_gas = y.accumulate_gas
        x.result = y.resultWorkReport.report.results, report[0].report.results

    Guarantee[0].slot = report[0].slot

    for x, y in zip(Guarantee[0].signatures, report[0].signatures):
        x.validator_index = y.validator_index
        x.signature = y.signature

    # input.slot remaining

    return Guarantee



class Reporting:

    @staticmethod
    def transition(self, pre_state:State, block:Block)->State:
        new_state:State = dataclasses.replace(pre_state)

        # State.rho
        # if new_state.rho[0] is not None:
        #     new_state.rho[0].report == workreport()
        # else:
        #     new_state.rho[0].time == slot


        Reporting.valid_report_fn(pre_state.alpha[0].AuthorizationPool)

        n = WorkReportState(generate_report(Block.extrinsic.guarantees),block.extrinsic.guarantees[0].slot)
        generate_report(Block.extrinsic.guarantees)
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

    @decodable_choice
    def package_ava_fn(self, availabilitly:())->{}:
        ...



    def refinement_fn(self, refinement_set) -> {}:


    def segement_root_lookup(self):
        ...

    def result_fn(self):

        for x in self.transition().rho:
            for y in x.report.results:
                if not y.accumulate_gas >= self.transition().delta[ServiceId].min_gas:
                    return 'err'
                total_accumulate_gas = sum + y.accumulate_gas
            if not sum <= ACCUMULATION_GAS:
                return 'err'








#
# test_instance = Rho
#     # Call the function and print the result
# result = test_instance.transition(State, Block )
# print(result)
