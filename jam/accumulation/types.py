from typing import Tuple, List, Set
from tsrkit_types import structure, TypedVector, Bytes, Uint
from jam.types.protocol.merkle import OptionHash
from jam.types.state.phi import Phi
from jam.types.work import WorkExecResult
from jam.types.protocol.core import WorkPackageHash
from jam.types.state.chi import Chi
from jam.types.protocol.core import ServiceId, Gas, OpaqueHash, Balance, ExportsRoot
from jam.types.state.delta import Delta
from jam.types.state.iota import Iota


# Accumulation Types
GasConsumed = List[Tuple[ServiceId, Gas]]
BeefyMap = Set[Tuple[ServiceId, OpaqueHash]]


@structure
class OperandTuple:
    h: WorkPackageHash
    e: ExportsRoot
    a: OpaqueHash
    o: Bytes
    y: OpaqueHash
    g: Gas
    d: WorkExecResult


class OperandTuples(TypedVector[OperandTuple]):
    ...


@structure
class DeferredTransfer:
    sender: ServiceId
    receiver: ServiceId
    amount: Balance
    memo: Bytes
    gas: Gas


class DeferredTransfers(TypedVector[DeferredTransfer]):
    ...


@structure
class StateContext:
    # d
    service_accounts: Delta
    # i
    validator_keys: Iota
    # q
    authorizer_keys: Phi
    # m, a, v, z
    privileges: Chi


class DeferredTransfers(TypedVector[DeferredTransfer]):
    ...


PreimageDict = Set[Tuple[ServiceId, Bytes]]


@structure
class AccuContextX:
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


@structure
class AccumulationContext:
    x: AccuContextX
    y: AccuContextX
