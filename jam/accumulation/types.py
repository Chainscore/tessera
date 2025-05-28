from dataclasses import dataclass
from typing import Tuple, List, Set
from jam.types.base import Int
from jam.types.protocol.merkle import OptionHash
from jam.types.state.phi import Phi
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.utils.json import JsonSerde
from jam.types.work.report import WorkPackageHash, WorkExecResult
from jam.types.state.chi import Chi
from jam.types.protocol.core import ServiceId, Gas, OpaqueHash, Balance, ExportsRoot
from jam.types.base.bytes.bytes import Bytes
from jam.types.state.delta import Delta
from jam.types.state.iota import Iota


# Accumulation Types
GasConsumed = List[Tuple[ServiceId, Gas]]
BeefyMap = Set[Tuple[ServiceId, OpaqueHash]]


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


@decodable_dataclass
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


@decodable_vector(DeferredTransfer)
class DeferredTransfers(Vector[DeferredTransfer]):
    ...


PreimageDict = Set[Tuple[ServiceId, Bytes]]


@decodable_dataclass
@dataclass
class AccuContextX(Codable, JsonSerde):
    #s
    s_index: ServiceId
    #u
    partial_state: StateContext
    #i
    i_index: ServiceId
    #t
    deferred_transfers: DeferredTransfers
    #y
    hash: OptionHash
    #p
    preimage: PreimageDict


@decodable_dataclass
@dataclass
class AccumulationContext(Codable, JsonSerde):
    x: AccuContextX
    y: AccuContextX
