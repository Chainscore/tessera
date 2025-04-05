from dataclasses import dataclass
from typing import Callable, Tuple
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.types.protocol.core import Gas
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json.serde import JsonSerde
from jam.utils.codec import Codable
from jam.types.base.string import String


@decodable_dataclass
@dataclass
class OpCode(Codable, JsonSerde):
    name: String
    fn: Callable[[Registers, Memory], Tuple[Registers, Memory]]
    gas: Gas
    is_terminating: bool
