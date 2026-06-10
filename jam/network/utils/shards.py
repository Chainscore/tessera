from jam.models.protocol.core import CoreIndex, ValidatorIndex
from jam.models.work.shard import ShardIndex

from jam.utils.chainspec import chain_config
from jam.utils.constants import ec_original_shards


# vi = (si - CI * t) % validators
def get_vi(
    shard_index: ShardIndex,
    core_index: CoreIndex,
    erasure_shards: int | None = None,
):
    total_shards = int(erasure_shards or chain_config.num_validators)
    original_shards = ec_original_shards(total_shards)
    validator_index = ValidatorIndex(
        (shard_index - core_index * original_shards) % total_shards
    )

    return validator_index


# si = (CI * t + vi) % validators
def get_si(
    validator_index: ValidatorIndex,
    core_index: CoreIndex,
    erasure_shards: int | None = None,
):
    total_shards = int(erasure_shards or chain_config.num_validators)
    original_shards = ec_original_shards(total_shards)
    shard_index = ShardIndex(
        (core_index * original_shards + validator_index) % total_shards
    )

    return shard_index
