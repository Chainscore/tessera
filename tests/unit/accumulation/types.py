from dataclasses import dataclass
import json
import os
from typing import List

from jam.state.components.nu import AllReadyWRs, Nu
from jam.state.components.phi import Phi
from jam.state.components.xi import Xi
from jam.types.base.integers.fixed import U32
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.base.sequences.array import Array, decodable_array
from jam.utils.constants import EPOCH_LENGTH
from jam.utils.json import JsonSerde
from jam.types.work.report import WorkPackageHash, WorkDependencies, WorkExecResult, WorkReports
from jam.state.components.chi import Chi
from jam.types.protocol.crypto import Entropy
from jam.types.protocol.core import ServiceId,Gas,U64,OpaqueHash,Balance
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.state.components.delta import Delta
from jam.state.components.iota import Iota


from typing import Optional



@decodable_dataclass
@dataclass
class OperandTuple(Codable, JsonSerde):
    o: WorkExecResult
    l: OpaqueHash
    a: Bytes
    k: WorkPackageHash
    
@decodable_vector(OperandTuple)
class OperandTuples(Vector[OperandTuple]):
    ...

@decodable_dataclass
@dataclass
class DeferredTransfer(Codable, JsonSerde):
    sender: ServiceId
    receiver: ServiceId
    amount: Balance
    memo: Bytes
    gas: Gas

@decodable_vector(DeferredTransfer)
class DeferredTransfers(Vector[DeferredTransfer]):
    ...

@dataclass
class StateContext(Codable,JsonSerde):
    service_accounts: Delta
    validator_keys: Iota
    authorizer_keys: Phi
    privileges: Chi

@dataclass
class AcclOutput(Codable,JsonSerde):
    service_id: ServiceId
    hash: OpaqueHash

@decodable_vector(AcclOutput)  # It should be a set
class AccCommitmentMap(Vector[AcclOutput]):
    ...

# @decodable_vector(AllReadyWRs)
# class ReadyQueue(Vector[AllReadyWRs]):
#     ...
#
# @decodable_array(EPOCH_LENGTH,WorkDependencies)
# class Accumulated(Array[WorkDependencies]):
#     ...

@decodable_dataclass
@dataclass
class InputService(Codable,JsonSerde):
    code_hash: OpaqueHash
    balance: U64
    min_item_gas: Gas
    min_memo_gas: Gas
    bytes: U64
    items: U32

@decodable_dataclass
@dataclass
class InputPreimage(Codable,JsonSerde):
    hash: OpaqueHash
    blob: Bytes

@decodable_vector(InputPreimage)
class InputPreimages(Vector[InputPreimage]):
    ...

@decodable_dataclass
@dataclass
class AccountData(Codable,JsonSerde):
    service: InputService
    preimages: InputPreimages
    
@decodable_dataclass
@dataclass
class Account(Codable,JsonSerde):
    id:ServiceId
    data:AccountData

@decodable_vector(Account)
class Accounts(Vector[Account]):
    ...

@decodable_dataclass
@dataclass
class Acc(Codable,JsonSerde):
    service_id: ServiceId
    gas: Gas

@decodable_vector(Acc)
class AlwaysAcc(Vector[Acc]):
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
    ready_queue: Nu
    accumulated: Xi
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
    data_dir = "tests/unit/accumulation/tiny_1203"
    # data_dir = "./tiny"
    # data_dir = "./tiny_1203"
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
                try:
                    tc = Testcase.from_json(data)
                    print(f"Decoded {file}")
                    result.append(tc)
                except Exception as e:
                    print(f"❌ Failed to decode {file}: {e}")
                    continue
    return result 

