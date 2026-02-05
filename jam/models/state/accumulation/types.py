from typing import Tuple, List, Set, Union
from tsrkit_types import structure, TypedVector, Bytes, Uint, Choice
from jam.state.partial import GhostPartial, PartialState
from jam.models.protocol.merkle import OptionHash
from jam.models.state.phi import Phi, AuthorizerHash
from jam.models.work import WorkExecResult
from jam.models.protocol.core import WorkPackageHash
from jam.models.state.chi import Chi
from jam.models.protocol.core import ServiceId, Gas, OpaqueHash, Balance, ExportsRoot
from jam.models.state.delta import Delta
from jam.models.state.iota import Iota
from jam.utils.constants import W_T


# Accumulation Types
GasConsumed = List[Tuple[ServiceId, Gas]]
BeefyMap = Set[Tuple[ServiceId, OpaqueHash]]

@structure
class OperandTuple:
    p: WorkPackageHash
    e: ExportsRoot
    a: AuthorizerHash
    y: OpaqueHash # payload_hash
    g: Uint # accumulate_gas of a work result / digest
    l: WorkExecResult
    t: Bytes # auth_output of work report

@structure
class DeferredTransfer:
    sender: ServiceId # s
    receiver: ServiceId # d
    amount: Balance # a
    memo: Bytes[W_T] # m
    gas: Gas # g

class AccumulationInput(Choice):
    """
    Set I = U U X

    Source: https://graypaper.fluffylabs.dev/#/1c979cb/179400179400?v=0.7.1
    """
    tuple: OperandTuple
    transfer: DeferredTransfer

class AccumulationInputs(TypedVector[AccumulationInput]):
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