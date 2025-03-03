from dataclasses import dataclass, field
import json
import os
from typing import List

# from jam.types.extrinsics.disputes import DisputesExtrinsic, Offenders
from jam.types.base.integers.fixed import U32
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.utils.json import JsonSerde
from jam.types.work.report import WorkReports
from jam.types.protocol.crypto import OpaqueHash
from jam.state.components.nu import AllReadyWRs
from jam.types.work.report import WorkDependencies
from jam.state.components.chi import Chi
from jam.types.protocol.service import ServiceInfo
from jam.types.protocol.crypto import Entropy
from jam.types.protocol.core import ServiceId
from typing import Optional

@decodable_vector(AllReadyWRs)
class ReadyQueue(Vector[AllReadyWRs]):
    ...

@decodable_vector(WorkDependencies)
class Accumulated(Vector[WorkDependencies]):
    ...

@decodable_vector(ServiceInfo)
class Accounts(Vector[ServiceInfo]):
    ...
@decodable_vector(ServiceId)
class AlwaysAcc(Vector[ServiceId]):
    ...

@decodable_dataclass
@dataclass
class Input(Codable, JsonSerde):
    slot: U32
    reports: WorkReports

@decodable_dataclass
@dataclass
class ChiCustom(Codable, JsonSerde):
    bless: ServiceId  # ChiM - manager that can alter Chi
    assign: ServiceId  # ChiA - can alter Delta
    designate: ServiceId  # ChiV - can alter Iota
    always_acc: AlwaysAcc  # ChiG -
    
@decodable_dataclass
@dataclass
class PreState(Codable, JsonSerde):
    slot: U32
    entropy: Entropy
    ready_queue: ReadyQueue
    accumulated: Accumulated
    privileges: ChiCustom
    accounts: Accounts

PostState=PreState


@decodable_dataclass
@dataclass
class Output(Codable,JsonSerde):
    ok: Entropy


@decodable_dataclass
@dataclass
class Testcase(Codable,JsonSerde):
    input: Input
    pre_state: PreState
    output: Output
    post_state: PostState

def get_testcases_starting_with(prefix: str = "", limit: int = 10) -> List[Testcase]:
    data_dir = "tests/unit/accumulation/tiny"
    result = []
    for index, file in enumerate(os.listdir(data_dir)):
        # print("File->", file)
        if len(result) >= limit:
            continue
        elif not file.startswith(prefix):
            continue
        elif file.endswith(".bin"):
            continue
        else:
            with open(os.path.join(data_dir, file), "r") as f:
                data = json.loads(f.read())
                # print("ReadyQueue->", data["pre_state"]["ready_queue"])
                try:
                    tc = Testcase.from_json(data)
                    print(f"Decoded {file}")
                    # print("Bhaiiii->",tc.pre_state.lambda_)
                    result.append(tc)
                except Exception as e:
                    print(f"❌ Failed to decode {file}: {e}")
                    continue
    return result 

