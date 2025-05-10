from dataclasses import dataclass
from typing_extensions import Optional

from jam.accumulation.types import StateContext
from jam.execution.pvm.memory import Memory
from jam.types.protocol.crypto import OpaqueHash
from jam.types.state.chi import Chi
from jam.types.state.delta import Delta

from jam.types.base.integers.general import Int
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.core import Balance, Gas, ProgramCounter, ServiceId, WorkPackageHash
from jam.types.state.iota import Iota
from jam.types.state.phi import Phi
from jam.types.work.report import WorkExecResult
from jam.types.work.segment import Segments
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.codec.codable import Codable
from jam.utils.json import JsonSerde
from jam.types.base.dictionary import Dictionary, decodable_dictionary

from typing import List
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
class preimage_dict(Dictionary[ServiceId,Bytes]):
    ...

@decodable_dataclass
@dataclass
class accu_Xcontext(Codable, JsonSerde):
    s_index: ServiceId
    partial_state: StateContext
    i_index: ServiceId
    deferred_transfers: DeferredTransfers
    hash: Optional[Bytes]
    preimage:preimage_dict

@decodable_dataclass
@dataclass
class StateContext(Codable,JsonSerde):
    service_accounts: Delta
    validator_keys: Iota
    authorizer_keys: Phi
    privileges: Chi


@decodable_dataclass
@dataclass
class accumulation_context(Codable, JsonSerde):
    x:accu_Xcontext
    y:accu_Xcontext



@decodable_dataclass
@dataclass
class OperandTuple(Codable, JsonSerde):
    d: WorkExecResult
    l: OpaqueHash
    a: Bytes
    k: WorkPackageHash




@decodable_vector(OperandTuple)
class OperandTuples(Vector[OperandTuple]):
    ...





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
