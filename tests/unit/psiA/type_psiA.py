# from ast import Bytes
from dataclasses import dataclass

from jam.types.base import decodable_dictionary, Dictionary
from jam.types.base.integers.fixed import U32, U64
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.core import Balance, Gas, ServiceId, WorkPackageHash
from jam.types.protocol.crypto import Entropy, OpaqueHash
from jam.types.state.chi import Chi
from jam.types.state.delta import Delta
from jam.types.state.iota import Iota
from jam.types.state.nu import Nu
from jam.types.state.phi import Phi
from jam.types.state.pi import Pi, AllServiceStats
from jam.types.state.xi import Xi
from jam.types.work.report import WorkExecResult, WorkReports
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json.serde import JsonSerde

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

@decodable_dictionary(OpaqueHash, Bytes, key_name="hash", value_name="blob")
class InputPreimages(Dictionary):
    ...

@decodable_dataclass
@dataclass
class AccountData(Codable,JsonSerde):
    service: InputService
    preimages: InputPreimages

@decodable_dictionary(ServiceId, AccountData, key_name="id", value_name="data")
class Accounts(Dictionary):
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
    statistics: AllServiceStats
    accounts: Accounts

PostState=PreState


@decodable_dataclass
@dataclass
class Output(Codable,JsonSerde):
    ok: Entropy


@decodable_dataclass
@dataclass
class TestcasePsiA(Codable,JsonSerde):
    input: Input
    pre_state: PreState
    output: Output
    post_state: PostState
