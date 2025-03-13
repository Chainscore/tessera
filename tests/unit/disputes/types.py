from dataclasses import dataclass, field
import json
import os
from typing import List, Set

from jam.types.extrinsics.disputes import DisputesExtrinsic, Offenders
from jam.types.base.integers.fixed import U32
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.state.components.rho import Rho
from jam.state.components.psi import Psi
from jam.state.components.kappa import Kappa
from jam.state.components.lambda_ import Lambda_

from jam.utils.json import JsonSerde

@decodable_dataclass
@dataclass
class Input(Codable, JsonSerde):
    disputes: DisputesExtrinsic

@decodable_dataclass
@dataclass
class PreState(Codable, JsonSerde):
    psi: Psi
    rho: Rho
    tau: U32
    kappa: Kappa
    lambda_: Lambda_ = field(metadata={"json_name": "lambda"})
   

@decodable_dataclass
@dataclass
class PostState(Codable, JsonSerde):
    psi: Psi
    rho: Rho
    tau: U32
    kappa: Kappa
    lambda_: Lambda_ = field(metadata={"json_name": "lambda"})

@decodable_dataclass
@dataclass
class Testcase(Codable,JsonSerde):
    input: Input
    pre_state: PreState
    output: dict
    post_state: PostState


def get_testcases_starting_with(prefix: str = "", limit: int = 10) -> List[Testcase]:
    data_dir = "/tests/unit/disputes/data/tiny"
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
                # print("data->", data["pre_state"]["lambda"])
                try:
                    tc = Testcase.from_json(data)
                    print(f"Decoded {file}")
                    # print("Bhaiiii->",tc.pre_state.lambda_)
                    result.append(tc)
                except Exception as e:
                    print(f"❌ Failed to decode {file}: {e}")
                    continue
    return result 
