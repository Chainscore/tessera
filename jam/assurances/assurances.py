from jam.types.block import Block
from jam.state.state import State
from jam.assurances.errors import AssurancesError
import dataclasses

class Assurances:
    """State transition function for the processing of Assurances."""

    @staticmethod
    def transition(state: State, block: Block) -> State:
        """Process the assurances extrinsic."""
        # Make a copy of the state
        new_state = dataclasses.replace(state)

        # Get the assurances from the extrinsic
        assurances = block.extrinsic.assurances

        rho = new_state.rho
        print("rho timeout", [r.timeout for r in rho])

        return new_state
        
