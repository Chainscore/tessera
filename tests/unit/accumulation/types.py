from dataclasses import dataclass, field
import json
import os
from typing import List

from jam.state.components.theta import AllReadyWRs
from jam.types.base.integers.fixed import U32
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.utils.json import JsonSerde
from jam.types.work.report import WorkReport
from jam.types.protocol.crypto import WorkReportHash
from jam.state.components.chi import Chi
from jam.types.protocol.service import ServiceInfo
from jam.types.protocol.crypto import Entropy
from jam.types.protocol.core import ServiceId,Gas,U64,OpaqueHash,Balance
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.state.components.delta import Delta
from jam.state.components.iota import Iota
from jam.state.components.xi import Xi

from typing import Optional


@decodable_dataclass
@dataclass
class DeferredTransfer(Codable,JsonSerde):
    sender: ServiceId
    receiver: ServiceId
    amount: Balance
    memo: Bytes
    gas: Gas

@dataclass
class stateContext(Codable,JsonSerde):
    service_accounts: Delta
    validator_keys: Iota
    authorizer_keys: Xi
    privileges: Chi

@dataclass
class AcclOutput(Codable,JsonSerde):
    service_id: ServiceId
    hash: OpaqueHash
@decodable_vector(AcclOutput)  # It should be a set
class AcclOutputs(Vector[AcclOutput]):
    ...

@decodable_vector(AllReadyWRs)
class ReadyQueue(Vector[AllReadyWRs]):
    ...
@decodable_vector(WorkReportHash)
class WorkDependencies(Vector[WorkReportHash]):
    ...
@decodable_vector(WorkDependencies)
class Accumulated(Vector[WorkDependencies]):
    ...

@decodable_dataclass
@dataclass
class customService(Codable,JsonSerde):
    code_hash:OpaqueHash
    balance:U64
    min_item_gas:Gas
    min_memo_gas:Gas
    bytes:U64
    items:U32

@decodable_dataclass
@dataclass
class customPreimage(Codable,JsonSerde):
    hash:OpaqueHash
    blob:Bytes

@decodable_vector(customPreimage)
class preimages(Vector[customPreimage]):
    ...

@decodable_dataclass
@dataclass
class accContents(Codable,JsonSerde):
    service:customService
    preimages:preimages
    
@decodable_dataclass
@dataclass
class AccountData(Codable,JsonSerde):
    id:ServiceId
    data:accContents

@decodable_vector(AccountData)
class Accounts(Vector[AccountData]):
    ...
@decodable_dataclass
@dataclass
class AlwaysAcc(Codable,JsonSerde):
    service_id: ServiceId
    gas: Gas

@decodable_vector(AlwaysAcc)
class AlwaysAcc(Vector[AlwaysAcc]):
    ...

@decodable_vector(WorkReport)
class WorkReports(Vector[WorkReport]):
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
    # data_dir="/home/akki/Codes/JAM/JamBhai/jam-node/tests/unit/accumulation/tiny"
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

