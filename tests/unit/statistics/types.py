import json
import os
from dataclasses import dataclass
from typing import List

from jam.state.components.tau import Tau
from jam.types.base import Nullable
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.block import Extrinsic
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.constants import VALIDATOR_COUNT
from jam.utils.json import JsonSerde


@decodable_dataclass
@dataclass
class ValidatorStat(Codable, JsonSerde):
    blocks: U32
    tickets: U32
    pre_images: U32
    pre_images_size: U32
    guarantees: U32
    assurances: U32


@decodable_array(VALIDATOR_COUNT, ValidatorStat)
class AllValidatorStats(Array[ValidatorStat]):
    """All validator stats"""

    ...


@decodable_dataclass
@dataclass
class Pi(Codable, JsonSerde):
    current: AllValidatorStats
    last: AllValidatorStats


@decodable_dataclass
@dataclass
class Input(Codable, JsonSerde):
    slot: U32
    author_index: U32
    extrinsic: Extrinsic


@decodable_dataclass
@dataclass
class PreState(Codable, JsonSerde):
    pi: Pi
    tau: Tau


PostState = PreState


@decodable_dataclass
@dataclass
class Testcase(Codable, JsonSerde):
    input: Input
    output: Nullable
    pre_state: PreState
    post_state: PostState


def get_testcases_starting_with(prefix: str = "", limit: int = 10) -> List[Testcase]:
    data_dir = "tests/unit/statistics/data/tiny"
    result = []
    for index, file in enumerate(os.listdir(data_dir)):
        if len(result) >= limit:
            continue
        elif not file.startswith(prefix):
            continue
        elif file.endswith(".bin"):
            continue
        else:
            with open(os.path.join(data_dir, file), "r") as f:
                data = json.loads(f.read())
                try:
                    tc = Testcase.from_json(data)
                    print(f"Decoded {file}")
                    result.append(tc)
                except Exception as e:
                    print(f"❌ Failed to decode {file}: {e}")
                    continue
    return result
