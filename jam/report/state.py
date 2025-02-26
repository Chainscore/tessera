from jam.state.components.rho import WorkReportState
from jam.state.state import State
from jam.types import Block, decodable_choice, ServiceId
import  dataclasses
from dataclasses import dataclass, replace

from jam.types.extrinsics import GuaranteesExtrinsic
from jam.utils.constants import ACCUMULATION_GAS, CORE_COUNT

def generate_report(report : GuaranteesExtrinsic)->WorkReportState.report:
    WorkReport: GuaranteesExtrinsic
    # for x in report:
    #     WorkReport.time = x.slot
    #     WorkReport.report = x.report

    WorkReport[0].report.package_spec.hash= report[0].report.package_spec.hash
    WorkReport[0].report.package_spec.length = report[0].report.package_spec.length
    WorkReport[0].report.package_spec.erasure_root = report[0].report.package_spec.erasure_root
    WorkReport[0].report.package_spec.exports_root = report[0].report.package_spec.exports_root
    WorkReport[0].report.package_spec.exports_count = report[0].report.package_spec.exports_count

    WorkReport[0].report.context.anchor = report[0].report.context.anchor
    WorkReport[0].report.context.state_root = report[0].report.context.state_root
    WorkReport[0].report.context.beefy_root = report[0].report.context.beefy_root
    WorkReport[0].report.context.lookup_anchor = report[0].report.context.lookup_anchor
    WorkReport[0].report.context.lookup_anchor_slot = report[0].report.context.lookup_anchor_slot
    WorkReport[0].report.context.lookup_anchor_slot = report[0].report.context.lookup_anchor_slot


    WorkReport[0].report.core_index = report[0].report.core_index
    WorkReport[0].report.authorizer_hash = report[0].report.authorizer_hash
    WorkReport[0].report.auth_output = report[0].report.auth_output
    WorkReport[0].report.segment_root_lookup = report[0].report.segment_root_lookup

    for x,y in zip(WorkReport[0].report.results,report[0].report.results):
        x.service_id = y.service_id
        x.code_hash = y.code_hash
        x.payload_hash = y.payload_hash
        x.accumulate_gas = y.accumulate_gas
        x.result = y.resultWorkReport.report.results,report[0].report.results

    WorkReport[0].slot = report[0].slot

    for x,y in zip(WorkReport[0].signatures,report[0].signatures):
        x.validator_index = y.validator_index
        x.signature = y.signature


    # input.slot remaining



    return WorkReport


class Report:
    @staticmethod
    def transition(self, pre_state:State, block:Block)->State:
        new_state:State = dataclasses.replace(pre_state)
        # # State.rho
        # if new_state.rho[0] is not None:
        #     new_state.rho[0].report == workreport()
        # else:
        #     new_state.rho[0].time == slot

        n = WorkReportState(
            generate_report(Block.extrinsic.guarantees),
            block.extrinsic.guarantees[0].slot
        )
        generate_report(Block.extrinsic.guarantees)
        return new_state

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


    def workreport(self, block:Block ) :
        # self.package_ava = self.package_ava_fn(package_ava)
        # self.refinement = self.refinement_fn(refinement)
        # self.core_index = core_index
        # self.auth_hash = auth_hash
        # self.auth_output = auth_output
        # self.segment_root_lookup = segment_root_lookup
        # self.result = self.result_fn()
        block.extrinsic.guarantees[0].report.








test_instance = Rho
    # Call the function and print the result
result = test_instance.transition(State, Block )
print(result)
