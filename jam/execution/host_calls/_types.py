from dataclasses import dataclass
from typing import List
from typing_extensions import Optional

from jam.accumulation.types import StateContext
from jam.execution.pvm.memory import Memory
from jam.types.base import decodable_choice, Choice
from jam.types.base.null import Nullable
from jam.types.protocol.crypto import OpaqueHash
from jam.types.state.chi import Chi
from jam.types.state.delta import Delta, AccountPreimages

from jam.types.base.integers.general import Int
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.core import Balance, Gas, ProgramCounter, ServiceId, WorkPackageHash, ExportsRoot
from jam.types.state.iota import Iota
from jam.types.state.phi import Phi
from jam.types.work.report import WorkExecResult
from jam.types.work.segment import Segments
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.codec.codable import Codable
from jam.utils.json import JsonSerde
from jam.types.base.dictionary import Dictionary, decodable_dictionary


from jam.types.base.integers.general import Int
from jam.types.base.sequences.bytes import ByteArray32, Byte, Bytes, ByteArray128
from jam.utils.json.decorators import with_json_metadata

from jam.types.state.delta import Timestamps
# from jam.state.components.delta import PartialState
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.core import Balance, Gas, ServiceId




#Refine Types



# Accumulation Types
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

@decodable_dictionary(ServiceId,Gas)
class service_dict(Dictionary[ServiceId,Gas]):
    ...

@decodable_dictionary(ServiceId,Bytes)
class PreimageDict(Dictionary[ServiceId,Bytes]):
    ...

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
    hash: Optional[Bytes]
    #p
    preimage:PreimageDict

@decodable_dataclass
@dataclass
class StateContext(Codable,JsonSerde):
    #d
    service_accounts: Delta
    #i
    validator_keys: Iota
    #q
    authorizer_keys: Phi
    #x
    privileges: Chi


@decodable_dataclass
@dataclass
class AccumulationContext(Codable, JsonSerde):
    x: AccuContextX
    y: AccuContextX



@decodable_dataclass
@dataclass
class OperandTuple(Codable, JsonSerde):
    d: WorkExecResult
    g: Gas
    y: OpaqueHash
    o: Bytes
    e: ExportsRoot
    h: WorkPackageHash
    a: Bytes


@decodable_vector(OperandTuple)
class OperandTuples(Vector[OperandTuple]):
    ...


@decodable_choice
class output(Choice):
    """Work execution result choice."""

    ok: Bytes
    out_of_gas: Nullable
    panic: Nullable


# @dataclass
# class AcclOutput(Codable,JsonSerde):
#     service_id: ServiceId
#     hash: OpaqueHash

# @decodable_vector(AcclOutput)  # It should be a set
# class AccCommitmentMap(Vector[AcclOutput]):
#     ...

##############################################


# # @decodable_dataclass
# # @dataclass
# # class BoldM(Codable, JsonSerde):
# #     blob: List
# #     memory: PageMemory
# #     i: Register


# # @decodable_dictionary(Int, BoldM)
# # class RefineMap(Dictionary[Int, BoldM]):
# #     ...

# #
# # @decodable_vector(element_type=Byte)
# # class SegEle(Vector[Byte]):
# #     ...
# #
# #
# # @decodable_vector(element_type=SegEle)
# # class Segment(Vector[SegEle]):
# #     ...


# @with_json_metadata(
#     sender={"name": "sender_index", "skip_if_none": True},
#     receiver={"name": "receiver_index", "skip_if_none": True},
#     amount={"name": "amount", "skip_if_none": True},
#     memo={"name": "memo", "skip_if_none": True},
#     gas={"name": "gas_limit", "skip_if_none": True}
# )




# # @decodable_vector(DeferredTransfer)
# # class DeferredTransfers(Vector[DeferredTransfer]):
# #     ...
