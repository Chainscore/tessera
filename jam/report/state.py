from jam.state.state import State
from jam.types import Block, decodable_choice
import  dataclasses
from dataclasses import dataclass, replace
class Rho:
    @staticmethod
    def transition(self, pre_state:State)->State:
        new_state:State = dataclasses.replace(pre_state)
        # State.rho
        if new_state.rho[0] is not None:
            new_state.rho[0].report == workreport()
        else
            new_state.rho[0].time == slot:

    @decodable_choice
    def package_ava_fn(self, header_hash, package_lenght, erasure_root, segment_root, segment_count)->{}:
        ...



    def refinement_fn(self, anchor, state_root, beffy_root, lookup_anchor_header, time_slot, prerequisites) -> {}:
        ...

    def segement_root_lookup(self):
        ...

    def result_fn(self):
        ...

    def workreport(self, package_ava, refinement, core_index, auth_hash, auth_output, segment_root_lookup, result ) :
        self.package_ava = self.package_ava_fn()
        self.refinement = self.refinement_fn()
        self.core_index = core_index
        self.auth_hash = auth_hash








test_instance = Rho
    # Call the function and print the result
result = test_instance.transition(State, Block )
print(result)
