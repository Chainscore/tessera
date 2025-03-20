from dataclasses import dataclass, field
from typing import List, Type, Any
from jam.types.base.integers.fixed import U32
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json.serde import JsonSerde, T
from jam.state.components.delta import Timestamps, AccountStorage, PreImageLookup, ServiceCodeHash, Balance
from jam.hostCall.context import Segment
from jam.types.protocol.core import Register
from jam.utils.json.decorators import with_json_metadata
from jam.types.base.dictionary import decodable_dictionary, Dictionary
from jam.types.base.string import String
from jam.types.base.sequences.bytes import ByteArray32
from jam.types.base.sequences.bytes.bytes import ByteVector32
from jam.types.protocol.core import Balance, BlobLength, Gas, ServiceId
from jam.types.protocol.validators import ValidatorsVector
from jam.state.components.phi import PhiVector
from jam.state.components.chi import Chi
from jam.pvm.pvm_memory import JsonPageMemory, JsonPages
from jam.types.base.sequences.vector import Vector


@decodable_dictionary(String, Register)
class TestRegister(Dictionary[String, Register]):
    ...


@with_json_metadata(
    t={"name": "t", "default": []}
)
@decodable_dataclass
@dataclass
class TestTimeStamp(Codable, JsonSerde):
    l: BlobLength
    t: Timestamps


@decodable_dictionary(ByteVector32, TestTimeStamp)
class TestLookup(Dictionary[ByteVector32, TestTimeStamp]):
    ...


@decodable_dataclass
@dataclass
class TestService(Codable, JsonSerde):
    s_map: AccountStorage
    p_map: PreImageLookup
    l_map: TestLookup
    code_hash: ByteVector32
    balance: Balance
    g: Gas
    m: Gas


@decodable_dictionary(String, TestService)
class TestDelta(Dictionary[String, TestService]):
    """Delta state"""
    ...


@decodable_dataclass
@dataclass
class TestPartialState(Codable, JsonSerde):
    D: TestDelta
    I: ValidatorsVector
    Q: PhiVector
    X: Chi


@with_json_metadata(
    T={"name": "T", "default": []},
    U={"name": "U", "skip_if_none": True, "default": TestPartialState(
                                D={},
                                I=ValidatorsVector(),
                                Q=PhiVector(),
                                X=Chi(
                                chi_m=U32(0),
                                chi_a=U32(0),
                                chi_v=U32(0),
                                chi_g={}
                                ),
                            )}
)
@decodable_dataclass
@dataclass
class TestXContent(Codable, JsonSerde):
    S: ServiceId
    U: TestPartialState
    I: ServiceId
    T: Timestamps
    Y: ByteVector32


@with_json_metadata(
    P={"name": "P", "default": Vector[int]([])}
)
@decodable_dataclass
@dataclass
class TestBoldM(Codable, JsonSerde):
    P: Vector
    U: JsonPageMemory
    I: Register


@decodable_dictionary(String, TestBoldM)
class TestRefineMap(Dictionary[String, TestBoldM]):
    ...


@with_json_metadata(
    initial_regs={"name": "initial-regs"},
    initial_gas={"name": "initial-gas"},
    initial_memory={"name": "initial-memory"},
    initial_service_account={"name": "initial-service-account", "skip_if_none": True, "default": {}},
    initial_service_index={"name": "initial-service-index", "skip_if_none": True, "default": 0},
    initial_delta={"name": "initial-delta", "skip_if_none": True, "default": {}},
    initial_xcontent_x={"name": "initial-xcontent-x", "skip_if_none": True, "default": {}},
    initial_xcontent_y={"name": "initial-xcontent-y", "skip_if_none": True, "default": {}},
    initial_refine_map={"name": "initial-refine-map", "skip_if_none": True, "default": {}},
    initial_export_segment={"name": "initial-export-segment", "skip_if_none": True, "default": {}},
    initial_export_segment_index={"name": "initial-export-segment-index", "skip_if_none": True, "default": 0},
    initial_timeslot={"name": "initial-timeslot", "skip_if_none": True, "default": []},
    expected_gas={"name": "expected-gas"},
    expected_regs={"name": "expected-regs"},
    expected_memory={"name": "expected-memory"},
    expected_service_account={"name": "expected-service-account", "skip_if_none": True, "default": {}},
    expected_delta={"name": "expected-delta", "skip_if_none": True, "default": {}},
    expected_xcontent_x={"name": "expected-xcontent-x", "skip_if_none": True, "default": {}},
    expected_xcontent_y={"name": "expected-xcontent-y", "skip_if_none": True, "default": {}},
    expected_refine_map={"name": "expected-refine-map", "skip_if_none": True, "default": {}},
    expected_export_segment={"name": "expected-export-segment", "skip_if_none": True, "default": {}},
)
# @with_json_metadata(
#     initial_regs={"name": "initial-regs", "default": {}},
#     initial_gas={"name": "initial-gas", "default": Gas(0)},
#     initial_memory={"name": "initial-memory", "default": JsonPageMemory({})},
#     initial_service_account={"name": "initial-service-account", "default": lambda: TestService(
#         s_map={},
#         p_map={},
#         l_map={},
#         code_hash=ByteVector32(),  # Assuming a 32-byte zeroed default
#         balance=Balance(0),
#         g=Gas(0),
#         m=Gas(0)
#     )},
#     initial_service_index={"name": "initial-service-index", "default": U32(0)},
#     initial_delta={"name": "initial-delta", "default": {}},
#     initial_xcontent_x={"name": "initial-xcontent-x",
#                         "default": lambda: TestXContent(
#                             S=ServiceId(0),
#                             U=TestPartialState(
#                                 D={},
#                                 I=ValidatorsVector(),
#                                 Q=PhiVector(),
#                                 X=Chi(
#                                 chi_m=U32(),
#                                 chi_a=U32(),
#                                 chi_v=U32(),
#                                 chi_g={}
#                                 ),
#                             ),
#                             I=ServiceId(0),
#                             T=Timestamps(list()),
#                             Y=ByteVector32(b"\x00" * 32)  # Assuming a 32-byte zeroed default
#                         )},
#     initial_xcontent_y={"name": "initial-xcontent-y",
#                         "default": lambda: TestXContent(
#                             S=ServiceId(0),
#                             U=TestPartialState(
#                                 D={},
#                                 I=ValidatorsVector(),
#                                 Q=PhiVector(),
#                                 X=Chi(
#                                 chi_m=U32(),
#                                 chi_a=U32(),
#                                 chi_v=U32(),
#                                 chi_g={}
#                                 ),
#                             ),
#                             I=ServiceId(0),
#                             T=Timestamps(list()),
#                             Y=ByteVector32(b"\x00" * 32)  # Assuming a 32-byte zeroed default
#                         )},
#     # initial_refine_map={"name": "initial-refine-map", "default": {}},
#     # initial_export_segment={"name": "initial-export-segment", "default": Segment(list())},
#     initial_export_segment_index={"name": "initial-export-segment-index", "default": U32(0)},
#     initial_timeslot={"name": "initial-timeslot", "default": Timestamps(list())},
#     expected_gas={"name": "expected-gas", "default": Gas(0)},
#     expected_regs={"name": "expected-regs", "default": {}},
#     expected_memory={"name": "expected-memory", "default": JsonPageMemory({})},
#     expected_service_account={"name": "expected-service-account", "default": lambda: TestService(
#         s_map={},
#         p_map={},
#         l_map={},
#         code_hash=ByteVector32(),  # Assuming a 32-byte zeroed default
#         balance=Balance(0),
#         g=Gas(0),
#         m=Gas(0)
#     )},
#     expected_delta={"name": "expected-delta", "default": {}},
#     expected_xcontent_x={"name": "expected-xcontent-x",
#                          "default": lambda: TestXContent(
#                             S=ServiceId(0),
#                             U=TestPartialState(
#                                 D={},
#                                 I=ValidatorsVector(),
#                                 Q=PhiVector(),
#                                 X=Chi(
#                                 chi_m=U32(),
#                                 chi_a=U32(),
#                                 chi_v=U32(),
#                                 chi_g={}
#                                 ),
#                             ),
#                             I=ServiceId(0),
#                             T=Timestamps(list()),
#                             Y=ByteVector32(b"\x00" * 32)  # Assuming a 32-byte zeroed default
#                         )},
#     expected_xcontent_y={"name": "expected-xcontent-y",
#                          "default": lambda: TestXContent(
#                             S=ServiceId(0),
#                             U=TestPartialState(
#                                 D={},
#                                 I=ValidatorsVector(),
#                                 Q=PhiVector(),
#                                 X=Chi(
#                                 chi_m=U32(),
#                                 chi_a=U32(),
#                                 chi_v=U32(),
#                                 chi_g={}
#                                 ),
#                             ),
#                             I=ServiceId(0),
#                             T=Timestamps(list()),
#                             Y=ByteVector32(b"\x00" * 32)  # Assuming a 32-byte zeroed default
#                         )},
#     # expected_refine_map={"name": "expected-refine-map", "default": {}},
#     # expected_export_segment={"name": "expected-export-segment", "default": Segment(list())},
# )
@decodable_dataclass
@dataclass
class TestCases(Codable, JsonSerde):
    initial_regs: TestRegister
    initial_memory: JsonPageMemory
    initial_gas: Gas
    initial_service_account: TestService
    initial_service_index: U32
    initial_delta: TestDelta
    initial_xcontent_x: TestXContent
    initial_xcontent_y: TestXContent
    initial_refine_map: TestRefineMap
    initial_export_segment: Segment
    initial_export_segment_index: U32
    initial_timeslot: Timestamps
    expected_regs: TestRegister
    expected_memory: JsonPageMemory
    expected_gas: Gas
    expected_service_account: TestService
    expected_delta: TestDelta
    expected_xcontent_x: TestXContent
    expected_xcontent_y: TestXContent
    expected_refine_map: TestRefineMap
    expected_export_segment: Segment
