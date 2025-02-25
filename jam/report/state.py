from jam.state.state import State
from jam.types import Block
import  dataclasses
from dataclasses import dataclass, replace
class Rho:
    @staticmethod
    def transition(self, pre_state:State, block:Block)->State:
        new_state:State = dataclasses.replace(pre_state)
        # State.rho
        if new_state.rho[0] is not None:
            print(new_state.rho[0].report)
        print(new_state.rho, "new state")
        return new_state.rho




test_instance = Rho
    # Call the function and print the result
result = test_instance.transition(State, Block )
print(result)
