from typing import Tuple, List, Set, Union
from tsrkit_types import structure, TypedVector, Bytes, Uint
from jam.state.partial import GhostPartial, PartialState
from jam.types.protocol.merkle import OptionHash
from jam.types.state.phi import Phi, AuthorizerHash
from jam.types.work import WorkExecResult
from jam.types.protocol.core import WorkPackageHash
from jam.types.state.chi import Chi
from jam.types.protocol.core import ServiceId, Gas, OpaqueHash, Balance, ExportsRoot
from jam.types.state.delta import Delta
from jam.types.state.iota import Iota


# Accumulation Types
GasConsumed = List[Tuple[ServiceId, Gas]]
BeefyMap = Set[Tuple[ServiceId, OpaqueHash]]

class OperandBase:
    pass

@structure
class OperandTuple(OperandBase):
    p: WorkPackageHash
    e: ExportsRoot
    a: AuthorizerHash
    y: OpaqueHash # payload_hash
    g: Uint # accumulate_gas of a work result / digest
    l: WorkExecResult
    t: Bytes # auth_output of work report

@structure
class DeferredTransfer(OperandBase):
    sender: ServiceId # s
    receiver: ServiceId # d
    amount: Balance # a
    memo: Bytes # m
    gas: Gas # g

class OperandTuples(TypedVector[OperandBase]):
    ...

class DeferredTransfers(TypedVector[DeferredTransfer]):
    ...


PreimageDict = Set[Tuple[ServiceId, Bytes]]


@structure
class AccuContextX:
    # s
    s_index: ServiceId
    # e
    partial_state: PartialState
    # i
    i_index: ServiceId
    # t
    deferred_transfers: DeferredTransfers
    # y
    hash: OptionHash
    # p
    preimage: PreimageDict


@structure
class AccumulationContext:
    x: AccuContextX
    y: AccuContextX


# @structure
# class AccumulationOutput:
#     e: StateContext # posterior state context
#     t: DeferredTransfers # deferred transfers
#     y: OptionHash # output hash
#     u: Gas # gas used
#     p: PreimageDict # new preimages ?

AccumulationOutput = Tuple[GhostPartial, DeferredTransfers, OptionHash, Gas, PreimageDict]