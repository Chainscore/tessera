from dataclasses import dataclass
import json
import os
from typing import List
from jam.state.components.alpha import Alpha
from jam.state.components.phi import Phi
from jam.types import CoreIndex, Vector, decodable_vector
from jam.types.base.integers.fixed import U32
from jam.types.protocol.crypto import Entropy, OpaqueHash
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde

@decodable_dataclass
@dataclass
class InputWorkReport(Codable, JsonSerde):
    """Input work report structure."""
    core: CoreIndex
    auth_hash: OpaqueHash

@decodable_vector(InputWorkReport)
class InputAuths(Vector): ...

@decodable_dataclass
@dataclass
class Input(Codable, JsonSerde):
    slot: U32
    auths: InputAuths

@decodable_dataclass
@dataclass
class PreState(Codable, JsonSerde):
    auth_pools: Alpha
    auth_queues: Phi
    
PostState = PreState

@decodable_dataclass
@dataclass
class Testcase(Codable, JsonSerde):
    input: Input
    pre_state: PreState
    post_state: PostState

def get_testcases_starting_with(prefix: str = "", limit: int = 10) -> List[Testcase]:
    data_dir = "tests/unit/authorization/data/tiny"
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