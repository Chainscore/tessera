from dataclasses import dataclass
import json
import os
from typing import List, Set

from jam.types.extrinsics.disputes import DisputesExtrinsic, Offenders
from jam.types.base.integers.fixed import U32
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.state.components.rho import Rho


@decodable_dataclass
@dataclass
class Input(Codable):
    slot: U32
    extrinsic: DisputesExtrinsic


@decodable_dataclass
@dataclass
class PreState(Codable):
    good: Set[bytes]
    bad: Set[bytes]
    wonky: Set[bytes]
    offenders: Offenders
    rho: Rho


@decodable_dataclass
@dataclass
class PostState(Codable):
    good: Set[bytes]
    bad: Set[bytes]
    wonky: Set[bytes]
    offenders: Offenders
    rho: Rho


@decodable_dataclass
@dataclass
class Testcase(Codable):
    input: Input
    pre_state: PreState
    output: dict
    post_state: PostState


def get_testcases_starting_with(prefix: str = "", limit: int = 10) -> List[Testcase]:
    data_dir = "tests/unit/disputes/data/tiny"
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