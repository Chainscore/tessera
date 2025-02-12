import dataclasses

from jam.types.block import Block
from jam.state.state import State
from jam.utils.constants import CORE_COUNT


class Authorization:
    @staticmethod
    def transition(pre_state: State, block: Block) -> State:
        """
        Transition the state with Authorization logic.

        Args:
            pre_state: State before transition
            block: Block

        Returns:
            State after transition
        """
        # Make a copy of the state
        new_state = dataclasses.replace(pre_state)

        if len(new_state.alpha) != CORE_COUNT:
            raise ValueError("Invalid alpha length, must be equal to CORE_COUNT")

        alpha_temp = new_state.alpha.value
        for i in range(CORE_COUNT):
            core_alpha_temp = alpha_temp[i].value
            # Pop out the executed authorizer from alpha
            authr = core_alpha_temp[0]
            for j in block.extrinsic.guarantees:
                if j.report.core_index == i:
                    authr = j.report.authorizer_hash
                    break
            indexToPop = core_alpha_temp.index(authr)
            core_alpha_temp.pop(indexToPop)
            # Push phi[c][Ht] to alpha
            core_alpha_temp.append(new_state.phi[i][block.header.slot.value])
            alpha_temp[i] = core_alpha_temp
        new_state.alpha = alpha_temp

        return new_state
