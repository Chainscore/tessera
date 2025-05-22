from dataclasses import dataclass

from jam.types.base import decodable_dictionary, Dictionary, Int
from jam.types.state.phi import Phi
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.utils.json import JsonSerde
from jam.types.work.report import WorkPackageHash, WorkExecResult
from jam.types.state.chi import Chi
from jam.types.protocol.core import ServiceId, Gas, OpaqueHash, Balance, ExportsRoot
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.state.delta import Delta
from jam.types.state.iota import Iota

@decodable_dataclass
@dataclass
class OperandTuple(Codable, JsonSerde):
    h: WorkPackageHash
    e: ExportsRoot
    a: OpaqueHash
    o: Bytes
    y: OpaqueHash
    g: Int
    d: WorkExecResult


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
    # d
    service_accounts: Delta
    # i
    validator_keys: Iota
    # q
    authorizer_keys: Phi
    # x
    privileges: Chi

# @dataclass
# class AcclOutput(Codable,JsonSerde):
#     service_id: ServiceId
#     hash: OpaqueHash

@decodable_dictionary(ServiceId,bytes)
class AccumulationOutput(Dictionary[ServiceId,bytes]): #U
    ...

@decodable_dataclass
@dataclass
class GasAccumulated(Codable, JsonSerde):
    service_id: ServiceId
    accumulated_gas: Gas

@decodable_vector(GasAccumulated)
class GasAccumulations(Vector[GasAccumulated]):
    ...

@decodable_dictionary(ServiceId,Bytes)
class PreimageDict(Dictionary[ServiceId,Bytes]):
    ...
