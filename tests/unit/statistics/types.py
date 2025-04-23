import json
import os
from dataclasses import dataclass
from typing import List

from jam.chainspec import CHAIN_SPEC
from jam.state.components.pi import AllCoreStats, AllValidatorStats, ServiceStat
from jam.state.components.tau import Tau
from jam.types.base import Nullable
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.block import Extrinsic
from jam.types.protocol.core import ServiceId
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde


@dataclass
class TestServiceRecord(Codable, JsonSerde):
    id: ServiceId
    record: ServiceStat


@decodable_vector(TestServiceRecord)
class TestServiceStats(Vector): ...


@decodable_dataclass
@dataclass
class Pi(Codable, JsonSerde):
    """Test Pi structure."""

    vals_current: AllValidatorStats
    vals_last: AllValidatorStats
    cores: AllCoreStats
    services: TestServiceStats


@decodable_dataclass
@dataclass
class Input(Codable, JsonSerde):
    slot: U32
    author_index: U32
    extrinsic: Extrinsic


@decodable_dataclass
@dataclass
class PreState(Codable, JsonSerde):
    statistics: Pi
    slot: Tau


PostState = PreState


@decodable_dataclass
@dataclass
class Testcase(Codable, JsonSerde):
    input: Input
    output: Nullable
    pre_state: PreState
    post_state: PostState


def get_testcases_starting_with(prefix: str = "", limit: int = 10) -> List[Testcase]:
    data_dir = f"tests/unit/statistics/data/{CHAIN_SPEC}"
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
