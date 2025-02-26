from jam.state.state import State
from jam.types import Block, decodable_choice, ServiceId
import  dataclasses
from dataclasses import dataclass, replace

from jam.utils.constants import ACCUMULATION_GAS


class Rho:
    @staticmethod
    def transition(self, pre_state:State)->State:
        new_state:State = dataclasses.replace(pre_state)
        # State.rho
        if new_state.rho[0] is not None:
            new_state.rho[0].report == workreport()
        else:
            new_state.rho[0].time == slot

        return new_state

    @decodable_choice
    def package_ava_fn(self, availabilitly:())->{}:
        ...



    def refinement_fn(self, refinement_set) -> {}:
        ...

    def segement_root_lookup(self):
        ...

    def result_fn(self):

        for x in self.transition().rho:
            for y in x.report.results:
                if not y.accumulate_gas >= self.transition().delta[ServiceId].min_gas:
                    return 'err'
                sum = sum + y.accumulate_gas
            if not sum <= ACCUMULATION_GAS:
                return 'err'


    def workreport(self, package_ava:(), refinement, core_index, auth_hash, auth_output, segment_root_lookup, result ) :
        self.package_ava = self.package_ava_fn(package_ava)
        self.refinement = self.refinement_fn(refinement)
        self.core_index = core_index
        self.auth_hash = auth_hash
        self.auth_output = auth_output
        self.segment_root_lookup = segment_root_lookup
        self.result = self.result_fn()








test_instance = Rho
    # Call the function and print the result
result = test_instance.transition(State, Block )
print(result)
