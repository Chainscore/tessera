from dataclasses import dataclass
import json
import os
from typing import List
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.jstruct import JsonSerde
from jam.types.extrinsics.assurances import AssurancesExtrinsic
from jam.state.components.rho import Rho
from jam.assurances.errors import AssurancesErrorCode
from jam.types.work.report import WorkReport
from jam.types import Vector, decodable_vector
from jam.types.protocol.core import TimeSlot, OpaqueHash
from jam.state.components.kappa import Kappa

@decodable_dataclass
@dataclass
class Input(Codable, JsonSerde):
    assurances: AssurancesExtrinsic
    slot: TimeSlot
    parent: OpaqueHash

@decodable_dataclass
@dataclass
class PreState(Codable, JsonSerde):
    avail_assignments: Rho
    curr_validators: Kappa

PostState = PreState

@decodable_vector(WorkReport)
class WorkOutputVector(Vector[WorkReport]):
    ...

@decodable_dataclass
@dataclass
class OkOutput(Codable, JsonSerde):
    reported: WorkOutputVector

@decodable_dataclass
@dataclass
class Output(Codable, JsonSerde):
    err: AssurancesErrorCode
    ok: OkOutput

@decodable_dataclass
@dataclass
class Testcase(Codable, JsonSerde):
    input: Input
    pre_state: PreState
    output: Output
    post_state: PostState

def get_testcases_starting_with(prefix: str = "", limit: int = 10) -> List[Testcase]:
    data_dir = "tests/unit/assurances/data/tiny"
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
