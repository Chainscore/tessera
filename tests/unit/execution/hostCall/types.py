from dataclasses import dataclass

from jam.types.base.dictionary import decodable_dictionary, Dictionary
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.bytes.bytes import ByteVector32, Bytes, Byte
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.base.string import String

from jam.types.protocol.core import Balance, BlobLength, Gas, ServiceId
from jam.types.protocol.core import Register

from jam.types.work.package import WorkPackage
from jam.types.work.segment import Segment

from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json.decorators import with_json_metadata
from jam.utils.json.serde import JsonSerde

from jam.types.state.delta import Timestamps, AccountStorage, AccountPreimages
from jam.types.protocol.validators import ValidatorVector
from jam.types.state.phi import PhiVector
from jam.types.state.chi import Chi
from jam.execution.pvm.memory import Memory
from jam.hostCall.types import DeferredTransfers


@decodable_dictionary(String, Register)
class TestRegister(Dictionary[String, Register]):
    ...


@with_json_metadata(
    t={"name": "t", "skip_if_none": True}
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
    p_map: AccountPreimages
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
    I: ValidatorVector
    Q: PhiVector
    X: Chi


@with_json_metadata(
    T={"name": "T", "skip_if_none": True},
    U={"name": "U", "skip_if_none": True}
)
@decodable_dataclass
@dataclass
class TestXContent(Codable, JsonSerde):
    S: ServiceId
    U: TestPartialState
    I: ServiceId
    T: DeferredTransfers
    Y: ByteVector32


@decodable_vector(element_type=Byte)
class JsonP(Vector[Byte]):
    ...


@with_json_metadata(
    P={"name": "P", "skip_if_none": True}
)
@decodable_dataclass
@dataclass
class TestBoldM(Codable, JsonSerde):
    P: JsonP
    U: Memory
    I: Register


@decodable_dictionary(String, TestBoldM)
class TestRefineMap(Dictionary[String, TestBoldM]):
    ...


@with_json_metadata(
    initial_regs={"name": "initial-regs"},
    initial_gas={"name": "initial-gas"},
    initial_memory={"name": "initial-memory"},
    initial_blob={"name": "initial-blob", "skip_if_none": True},
    initial_service_account={"name": "initial-service-account", "skip_if_none": True},
    initial_service_index={"name": "initial-service-index", "skip_if_none": True},
    initial_delta={"name": "initial-delta", "skip_if_none": True},
    initial_xcontent_x={"name": "initial-xcontent-x", "skip_if_none": True},
    initial_xcontent_y={"name": "initial-xcontent-y", "skip_if_none": True},
    initial_refine_map={"name": "initial-refine-map", "skip_if_none": True},
    initial_export_segment={"name": "initial-export-segment", "skip_if_none": True},
    initial_export_segment_index={"name": "initial-export-segment-index", "skip_if_none": True},
    initial_work_package={"name": "initial-work-package", "skip_if_none": True},
    initial_timeslot={"name": "initial-timeslot", "skip_if_none": True},
    expected_gas={"name": "expected-gas"},
    expected_regs={"name": "expected-regs"},
    expected_memory={"name": "expected-memory"},
    expected_service_account={"name": "expected-service-account", "skip_if_none": True},
    expected_delta={"name": "expected-delta", "skip_if_none": True},
    expected_xcontent_x={"name": "expected-xcontent-x", "skip_if_none": True},
    expected_xcontent_y={"name": "expected-xcontent-y", "skip_if_none": True},
    expected_refine_map={"name": "expected-refine-map", "skip_if_none": True},
    expected_export_segment={"name": "expected-export-segment", "skip_if_none": True},
)
@decodable_dataclass
@dataclass
class TestCases(Codable, JsonSerde):
    initial_regs: TestRegister
    initial_memory: Memory
    initial_gas: Gas
    initial_service_account: TestService
    initial_service_index: U32
    initial_delta: TestDelta
    initial_xcontent_x: TestXContent
    initial_xcontent_y: TestXContent
    initial_refine_map: TestRefineMap
    initial_export_segment: Segment
    initial_export_segment_index: U32
    initial_work_package: WorkPackage
    initial_blob: Bytes
    initial_timeslot: U32
    expected_regs: TestRegister
    expected_memory: Memory
    expected_gas: Gas
    expected_service_account: TestService
    expected_delta: TestDelta
    expected_xcontent_x: TestXContent
    expected_xcontent_y: TestXContent
    expected_refine_map: TestRefineMap
    expected_export_segment: Segment
