
from dataclasses import dataclass
from typing import Any, Sequence, Tuple

from jam.types.base.bytes import Bytes
from jam.types.base.integers import U16
from jam.types.protocol.core import ErasureRoot, ExportsRoot, TimeSlot
from jam.types.protocol.validators import ValidatorArray
from jam.utils.codec.base import Codable
from jam.types.protocol.crypto import (
    BandersnatchPublic, BandersnatchVrfSignature,
    HeaderHash, StateRoot, OpaqueHash, Entropy,
    BeefyRoot
)
from jam.utils.constants import VALIDATOR_COUNT

@dataclass
class Header(Codable):
    """Block header structure."""
    slot: TimeSlot
    parent: HeaderHash
    state_root: StateRoot
    beefy_root: BeefyRoot
    exports_root: ExportsRoot
    erasure_root: ErasureRoot
    entropy: Entropy
    tickets_entropy: Entropy
    validators: ValidatorArray
    vrf_signature: BandersnatchVrfSignature
    extrinsic_root: OpaqueHash
    extrinsic_count: U16

    def enc_sequence(self) -> Sequence[Codable]:
        sequence = [
            self.slot, self.parent, self.state_root, self.beefy_root,
            self.exports_root, self.erasure_root, self.entropy,
            self.tickets_entropy, self.extrinsic_root, self.extrinsic_count
        ]
        sequence.extend(self.validators)
        sequence.append(self.vrf_signature)
        return sequence

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
        slot, size = TimeSlot.decode_from(buffer, current_offset)
        current_offset += size
        parent, size = HeaderHash.decode_from(buffer, current_offset)
        current_offset += size
        state_root, size = StateRoot.decode_from(buffer, current_offset)
        current_offset += size
        beefy_root, size = BeefyRoot.decode_from(buffer, current_offset)
        current_offset += size
        exports_root, size = ExportsRoot.decode_from(buffer, current_offset)
        current_offset += size
        erasure_root, size = ErasureRoot.decode_from(buffer, current_offset)
        current_offset += size
        entropy, size = Entropy.decode_from(buffer, current_offset)
        current_offset += size
        tickets_entropy, size = Entropy.decode_from(buffer, current_offset)
        current_offset += size
        extrinsic_root, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        extrinsic_count, size = U16.decode_from(buffer, current_offset)
        current_offset += size

        validators = []
        while current_offset < len(buffer) and len(validators) < VALIDATOR_COUNT:
            validator, size = BandersnatchPublic.decode_from(buffer, current_offset)
            validators.append(validator)
            current_offset += size

        vrf_signature, size = BandersnatchVrfSignature.decode_from(buffer, current_offset)
        current_offset += size

        return Header(slot, parent, state_root, beefy_root, exports_root,
                     erasure_root, entropy, tickets_entropy,
                     ValidatorArray(validators), vrf_signature,
                     extrinsic_root, extrinsic_count), current_offset - offset

