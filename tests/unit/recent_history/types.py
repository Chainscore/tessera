import os
import json

from jam.state.state import State
from jam.merklization import MMR
from jam.types.base.sequences.vector import decodable_vector, Vector
from jam.utils.codec import Codable
from jam.utils.json import JsonSerde
from jam.utils.codec.decorators import decodable_dataclass
from jam.types.protocol.crypto import OpaqueHash, HeaderHash, StateRoot
from dataclasses import dataclass
from jam.state.components.beta import PackageDict, Beta, BlockHistory
from jam.types.protocol.core import (
    SegmentRoot,
    WorkPackageHash,
)
from typing import List

@decodable_dataclass
@dataclass
class WorkPackage(Codable, JsonSerde):
    """Input Work Packages Structure"""

    hash: OpaqueHash
    exports_root: OpaqueHash

@decodable_vector(WorkPackage)
class PackageDictInput(Vector):
    """Work Packages Input for Recent History"""

    def to_dict(self)->PackageDict:
        package_dict: PackageDict[WorkPackageHash, SegmentRoot] = PackageDict()

        for pair in self:
            key = pair.hash
            value = pair.exports_root
            package_dict[key]=value

        return package_dict

@decodable_dataclass
@dataclass
class MMRInput(Codable, JsonSerde):
    """Input Structure for MMR Peaks in Block History for Recent History"""
    peaks: MMR

    def to_mmr(self) -> MMR:
        return self.peaks


@decodable_dataclass
@dataclass
class BlockHistoryInput(Codable, JsonSerde):
    """Block History Item in test vectors for Recent History"""

    header_hash: HeaderHash
    mmr: MMRInput
    state_root: StateRoot
    reported: PackageDictInput


@decodable_dataclass
@dataclass
class Input(Codable, JsonSerde):
    """Input format in test vectors for Recent History"""

    header_hash: OpaqueHash
    parent_state_root: OpaqueHash
    accumulate_root: OpaqueHash
    work_packages: PackageDictInput


@decodable_vector(BlockHistoryInput)
class BetaInput(Vector[BlockHistoryInput]):
    """Beta format in test vectors for Recent History"""

    def to_beta(self)->Beta:
        """Function to convert Beta from Input Format to System Format"""

        b= Beta([])
        for h in self:
            block_history = BlockHistory(h.header_hash, h.mmr.peaks, h.state_root, h.reported.to_dict())
            b.append(block_history)

        return b

@decodable_dataclass
@dataclass
class PreState(Codable, JsonSerde):
    """Pre State format in test vectors for Recent History"""
    beta:BetaInput

    def to_state(self) -> State:
        state = State()
        state.beta = self.beta.to_beta()
        return state

PostState = PreState

@decodable_dataclass
@dataclass
class Testcase(Codable, JsonSerde):
    """Testcase format in test vectors for Recent History"""
    input: Input
    pre_state: PreState
    post_state: PostState

def get_testcases_starting_with(prefix: str = "", limit: int = 0) -> List[Testcase]:
    """Read test vectors from data module"""

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
                    print(f"Decoded {tc}")
                    result.append(tc)
                except Exception as e:
                    print(f"❌ Failed to decode {file}: {e}")
                    continue
    return result