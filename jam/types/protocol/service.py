from dataclasses import dataclass
from jam.types.base.integers import U32, U64
# from jam.utils.codec import Codable
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import Gas
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass

@decodable_dataclass
@dataclass
class ServiceInfo(Codable):
    """Service information structure."""
    code_hash: OpaqueHash
    balance: U64
    min_item_gas: Gas
    min_memo_gas: Gas
    bytes_data: U64
    items: U32