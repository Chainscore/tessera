from dataclasses import dataclass
from jam.types.state.phi import Phi
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.utils.json import JsonSerde
from jam.types.work.report import WorkPackageHash, WorkExecResult
from jam.types.state.chi import Chi
from jam.types.protocol.core import ServiceId,Gas,OpaqueHash,Balance
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.state.delta import Delta
from jam.types.state.iota import Iota

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