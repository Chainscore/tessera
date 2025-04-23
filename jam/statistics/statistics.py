import dataclasses
from copy import deepcopy

from jam.state.components.pi import ValidatorStat
from jam.state.components.sigma import Sigma
from jam.types.block import Block
from jam.utils.constants import EPOCH_LENGTH


def create_empty_validator_stat():
    """Returns a new ValidatorStat object with all values set to 0."""
    return ValidatorStat(
        blocks=0,
        tickets=0,
        pre_images=0,
        pre_images_size=0,
        guarantees=0,
        assurances=0,
    )


class Statistics:
    @staticmethod
    def transition(pre_state: Sigma, block: Block) -> Sigma:
        """
        Transition the state with Statistics logic.

        Args:
            pre_state: State before transition
            block: Block

        Returns:
            State after transition
        """
        new_state = deepcopy(pre_state)

        if len(new_state.pi) != 2:
            raise ValueError("Invalid pi length, must be equal to 2")

        e = pre_state.tau // EPOCH_LENGTH
        e_dash = block.header.slot // EPOCH_LENGTH

        is_new_epoch = e != e_dash

        if is_new_epoch:
            pi_last = deepcopy(new_state.pi[0])
            pi_curr = deepcopy(new_state.pi[0])

            for i in range(len(pi_curr)):
                pi_curr[i] = create_empty_validator_stat()
        else:
            pi_curr = deepcopy(new_state.pi[0])
            pi_last = deepcopy(new_state.pi[1])

        author_index = block.header.author_index

        pi_curr[author_index].blocks += 1
        pi_curr[author_index].tickets += len(block.extrinsic.tickets)
        pi_curr[author_index].pre_images += len(block.extrinsic.preimages)

        for preimage in block.extrinsic.preimages:
            pi_curr[author_index].pre_images_size += len(preimage.blob)

        for guarantee in block.extrinsic.guarantees:
            signatures = guarantee.signatures
            for signature in signatures:
                validator_index = signature.validator_index
                pi_curr[validator_index].guarantees += 1

        for assurance in block.extrinsic.assurances:
            validator_index = assurance.validator_index
            pi_curr[validator_index].assurances += 1

        new_state.pi[0] = pi_curr
        new_state.pi[1] = pi_last

        return new_state
