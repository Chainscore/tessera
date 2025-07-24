from jam.types.state.alpha import Alpha, AuthorizationPool
from jam.types.state.sigma import Sigma
from jam.block import Block
from jam.utils.constants import CORE_COUNT


class Authorization:
    @staticmethod
    def transition(state: Sigma, block: Block) -> Sigma:
        """
        Transition the state with Authorization logic.

        Args:
            state: State before transition
            block: Block

        Returns:
            State after transition
        """
        if len(state.alpha) != CORE_COUNT:
            raise ValueError("Invalid alpha length, must be equal to CORE_COUNT")

        alpha_temp = state.alpha
        for i in range(CORE_COUNT):
            core_alpha_temp = alpha_temp[i]
            if len(core_alpha_temp) == 0:
                continue
            # Pop out the executed authorizer from alpha
            # We know it is executed from the report extrinsic
            # https://graypaper.fluffylabs.dev/#/5f542d7/109a0010a200
            authr = core_alpha_temp[0]
            for j in block.extrinsic.guarantees:
                if j.report.core_index == i:
                    authr = j.report.authorizer_hash
                    break
            indexToPop = core_alpha_temp.index(authr)
            core_alpha_temp.pop(indexToPop)
            # Push an authorizer from posterior phi[c] to alpha[c]
            # Phi is a circular array, so we need to take the modulo of the current slot
            # https://graypaper.fluffylabs.dev/#/5f542d7/107300107a00
            core_alpha_temp.append(state.phi[i][block.header.slot % len(state.phi[i])])
            alpha_temp[i] = AuthorizationPool(core_alpha_temp)

        state.alpha = Alpha(alpha_temp)

        return state
