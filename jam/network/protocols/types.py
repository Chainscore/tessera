from dataclasses import dataclass

from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.utils.json import JsonSerde

from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import HeaderHash
from jam.types import Header

@decodable_dataclass
@dataclass
class Final(Codable, JsonSerde):
    block_hash: HeaderHash
    time_slot: TimeSlot

@decodable_dataclass
@dataclass
class BlockAnnouncement(Codable, JsonSerde):
    header: Header
    final: Final