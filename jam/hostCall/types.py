from dataclasses import dataclass
from typing import List

from jam.accumulation.types import StateContext
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.integers.general import Int
from jam.types.base.sequences.bytes import ByteArray32, Byte, Bytes, ByteArray128
from jam.utils.json.decorators import with_json_metadata
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde
from jam.types.state.delta import Timestamps
# from jam.types.state.delta import PartialState
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.core import Balance, Gas, ServiceId
from jam.pvm.register import Register
from jam.pvm.pvm_memory import PageMemory
ServiceCodeHash = ByteArray32


@decodable_dataclass
@dataclass
class BoldM(Codable, JsonSerde):
    blob: List
    memory: PageMemory
    i: Register


@decodable_dictionary(Int, BoldM)
class RefineMap(Dictionary[Int, BoldM]):
    ...

#
# @decodable_vector(element_type=Byte)
# class SegEle(Vector[Byte]):
#     ...
#
#
# @decodable_vector(element_type=SegEle)
# class Segment(Vector[SegEle]):
#     ...


@with_json_metadata(
    sender={"name": "sender_index", "skip_if_none": True},
    receiver={"name": "receiver_index", "skip_if_none": True},
    amount={"name": "amount", "skip_if_none": True},
    memo={"name": "memo", "skip_if_none": True},
    gas={"name": "gas_limit", "skip_if_none": True}
)

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
class XContent(Codable, JsonSerde):
    s_index: ServiceId
    partial_state: StateContext
    i_index: ServiceId
    deferred_transfers: DeferredTransfers
    hash: ByteArray32
