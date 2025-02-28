from jam.types.block import Block
from jam.state.state import State


class Assurances:
    """State transition function for the processing of Assurances."""

    @staticmethod
    def transition(state: State, block: Block) -> State:
        """Process the assurances extrinsic."""
        ...