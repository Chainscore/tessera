from dataclasses import dataclass
from typing import List, Any, Tuple, Sequence
from jam.types.base.choice import Choice
from jam.types.base.integers import U32
from jam.types.base.array import Array
from jam.types.base.null import Null
from jam.types.work import WorkReport
from jam.utils.codec.base import Codable
from jam.utils.codec.composite.choices import ChoiceCodec
from jam.utils.constants import CORE_COUNT

@dataclass
class AvailabilityAssignment(Codable):
    """Availability assignment structure."""
    report: WorkReport
    timeout: U32

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.report, self.timeout]

    def encode_size(self) -> int:
        return sum(item.encode_size() for item in self.enc_sequence())

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        for item in self.enc_sequence():
            size = item.encode_into(buffer, current_offset)
            current_offset += size
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        current_offset = offset
        report, size = WorkReport.decode_from(buffer, current_offset)
        current_offset += size
        timeout, size = U32.decode_from(buffer, current_offset)
        current_offset += size
        return AvailabilityAssignment(report, timeout), current_offset - offset

class AvailabilityAssignments(Array[Choice]):
    """Fixed-size array of availability assignments."""
    def __init__(self, entries: List[Choice]):
        super().__init__(CORE_COUNT, entries)

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        entries, size = ChoiceCodec.decode_from([Null, AvailabilityAssignment], buffer, offset)
        return AvailabilityAssignments(entries), size
