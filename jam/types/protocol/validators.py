from dataclasses import field

from tsrkit_types.sequences import TypedArray
from tsrkit_types.integers import Uint, U8
from tsrkit_types.struct import structure
from jam.types.protocol.crypto import BandersnatchPublic, Ed25519Public, BlsPublic
from jam.utils.constants import VALIDATOR_COUNT
from tsrkit_types.bytes import Bytes

IPAddress = TypedArray[U8, 4]

@structure
class ValidatorMetadata:
    """Validator metadata structure Byte-Array(128)"""
    # NOTE - Could define fns to parse metadata into a more useful format
    name: Bytes[10]     # 10 Bytes
    protocol: Uint[16]  # 2 Bytes
    host: IPAddress     # 4 Bytes
    port: Uint[16]      # 2 Bytes
    buffer: Bytes[110] = field(metadata={"default": Bytes[110](110)})

    @property
    def address(self) -> str:
        res = "http://" if self.protocol == 2**16 - 1 else "https://"
        res += ".".join([str(ip) for ip in self.host])
        res += f":{int(self.port)}"
        return res

    @classmethod
    def from_json(cls, hex_data) -> "ValidatorMetadata":
        return cls.decode(Bytes.from_json(hex_data))


@structure
class ValidatorData:
    """Validator data structure."""

    bandersnatch: BandersnatchPublic
    ed25519: Ed25519Public
    bls: BlsPublic
    metadata: ValidatorMetadata


"""Fixed-size array of validator data with size VALIDATOR_COUNT."""
ValidatorsData = TypedArray[ValidatorData, VALIDATOR_COUNT]
