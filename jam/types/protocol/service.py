from tsrkit_types.integers import Uint
from tsrkit_types.struct import structure
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import Gas


@structure
class ServiceInfo:
    """Service information structure."""

    code_hash: OpaqueHash
    balance: Uint[64]
    min_item_gas: Gas
    min_memo_gas: Gas
    bytes_data: Uint[64]
    items: Uint[32]
