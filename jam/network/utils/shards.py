from jam.models.protocol.core import CoreIndex, ValidatorIndex
from jam.models.work.shard import ShardIndex

from jam.utils import constants
from jam.utils.chainspec import chain_config


# vi = (si - CI * t) % validators
def get_vi(shard_index: ShardIndex, core_index: CoreIndex):
    validator_index = ValidatorIndex(
        (shard_index - core_index * chain_config.recovery_threshold)
        % constants.VALIDATOR_COUNT
    )

    return validator_index


# si = (CI * t + vi) % validators
def get_si(validator_index: ValidatorIndex, core_index: CoreIndex):
    shard_index = ShardIndex(
        (core_index * chain_config.recovery_threshold + validator_index)
        % constants.VALIDATOR_COUNT
    )

    return shard_index
