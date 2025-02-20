from dataclasses import dataclass
import json
import os
from typing import List
from jam.state.components.alpha import Alpha
from jam.state.components.phi import Phi
from jam.types import CoreIndex, Vector, decodable_vector
from jam.types.base.integers.fixed import U32
from jam.types.protocol import MMR
from jam.types.protocol.crypto import Entropy, OpaqueHash, HeaderHash, StateRoot
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde
from jam.state.components.beta import PackageDict, Beta, BlockHistory

@decodable_dataclass
@dataclass
class Input(Codable, JsonSerde):
    header_hash:OpaqueHash
    parent_state_root:OpaqueHash
    accumulate_root:OpaqueHash
    work_packages: PackageDict

@decodable_dataclass
@dataclass
class InputReported(Codable, JsonSerde):
    """Input work report structure."""

    hash: OpaqueHash
    exports_root: OpaqueHash

@decodable_vector(InputReported)
class PackageDictInput(Vector):
    ...

@decodable_dataclass
@dataclass
class BlockHistoryInput(Codable, JsonSerde):
    """Block history item"""

    header_hash: HeaderHash
    mmr: MMR
    state_root: StateRoot
    packages: PackageDictInput


@decodable_vector(BlockHistoryInput)
class BetaInput(Vector[BlockHistoryInput]): ...

@decodable_dataclass
@dataclass
class PreState(Codable, JsonSerde):

    beta:BetaInput
    # for x in beta:
    #     x.:BlockHistoryInput.header_hash
    #     x.state_root:BlockHistoryInput.state_root
    #     x.reported:BlockHistoryInput.packages
    #     x.mmr.peaks:BlockHistoryInput.mmr_root


PostState = PreState





@decodable_dataclass
@dataclass
class Testcase(Codable, JsonSerde):
    input: Input
    pre_state: PreState
    post_state: PostState


def get_testcases_starting_with(prefix: str = "", limit: int = 8) -> List[Testcase]:
    data_dir = "tests/unit/recent_history/data/tiny"
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
