from dataclasses import dataclass

from jam.types import decodable_option, Option
from jam.types.base.choices import Choice
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.work import WorkReport
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.constants import CORE_COUNT
from jam.utils.jstruct.serde import JsonSerde






@decodable_dataclass
@dataclass
class AvailabilityAssignment(Codable, JsonSerde):
    """Availability assignment structure."""

    report: WorkReport
    timeout: U32
@decodable_option(AvailabilityAssignment)
class AvailabilityOption(Option): ...

"""Fixed-size array of availability assignments."""


@decodable_array(length=CORE_COUNT, element_type=AvailabilityOption)
class AvailabilityAssignments(Array[AvailabilityOption]):
    ...
