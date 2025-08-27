from dataclasses import field
from typing import Union

from tsrkit_types.sequences import TypedArray
from tsrkit_types.integers import Uint, U8
from tsrkit_types.struct import structure
from jam.types.protocol.crypto import BandersnatchPublic, Ed25519Public, BlsPublic
from jam.utils.constants import VALIDATOR_COUNT
from tsrkit_types.bytes import Bytes


class IPAddress(TypedArray[U8, 4]):
    def __str__(self):
        return ".".join(str(int(octet)) for octet in self)

    @classmethod
    def from_str(cls, ip_str: str) -> "IPAddress":
        parts = ip_str.strip().split(".")
        if len(parts) != 4:
            raise ValueError(f"Invalid IP format: {ip_str}")

        octets = [U8(int(part)) for part in parts]

        return cls(octets)


@structure
class ValidatorMetadata:
    """Validator metadata structure Byte-Array(128)"""

    # NOTE - Could define fns to parse metadata into a more useful format
    name: Bytes[10]  # 10 Bytes
    protocol: Uint[16]  # 2 Bytes
    host: IPAddress  # 4 Bytes
    port: Uint[16]  # 2 Bytes
    buffer: Bytes[110] = field(metadata={"default": Bytes[110](110)})

    @property
    def address(self) -> str:
        res = "http://" if self.protocol == 2**16 - 1 else "https://"
        res += ".".join([str(int(ip)) for ip in self.host])
        res += f":{int(self.port)}"
        return res

    @classmethod
    def from_json(cls, hex_data) -> "ValidatorMetadata":
        return cls.decode(Bytes.from_json(hex_data))

    def to_json(self) -> str:
        return self.encode().hex()


@structure
class ValidatorData:
    """Validator data structure."""

    bandersnatch: BandersnatchPublic
    ed25519: Ed25519Public
    bls: BlsPublic
    metadata: ValidatorMetadata

    def __hash__(self):
        return hash(self.encode())

    def __repr__(self):
        return (
            f"Validator(host={str(self.metadata.host)}, port={int(self.metadata.port)})"
        )


"""Fixed-size array of validator data with size VALIDATOR_COUNT."""
class ValidatorsData(TypedArray[ValidatorData, VALIDATOR_COUNT]):
    def find(self, key: BandersnatchPublic|Ed25519Public) -> Union[int, ValidatorData]:
        for i, validator in enumerate(self):
            if validator.bandersnatch == key or validator.ed25519 == key:
                return i, validator
        return -1, None
