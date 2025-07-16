from tsrkit_types.bytes import Bytes
from jam.types.state.gamma import GammaSTickets
import json
from typing import Optional
from jam.block.errors import BlockError, BlockErrorCode
from jam.block.extrinsics.extrinsic import Extrinsic
from jam.block.extrinsics.tickets import TicketEnvelope
from jam.types.state.gamma import GammaSFallback
from jam.utils.constants import EPOCH_LENGTH, X
from tsrkit_types import Option, structure
from jam.types import (
    BandersnatchVrfSignature,
    Hash,
    HeaderHash,
    StateRoot,
    OpaqueHash,
    TimeSlot,
    ValidatorIndex,
)
from dot_ring.vrf.ring.ring_vrf import RingVrf
from dot_ring.vrf.ietf.ietf import IETF_VRF

from .epoch_mark import EpochMark
from .offenders_mark import OffendersMark
from .tickets_mark import TicketsMark
from py_ark_vrf import prove_ietf, vrf_output, verify_ietf


@structure
class Header:
    """Block header structure."""

    parent: HeaderHash
    parent_state_root: StateRoot
    extrinsic_hash: OpaqueHash
    slot: TimeSlot
    epoch_mark: EpochMark
    tickets_mark: TicketsMark
    offenders_mark: OffendersMark
    author_index: ValidatorIndex
    entropy_source: BandersnatchVrfSignature
    seal: BandersnatchVrfSignature

    def __hash__(self) -> int:
        return int.from_bytes(self.hash())

    def encode_unsigned(self) -> bytes:
        return self.encode()[:-96]

    def hash(self) -> bytes:
        return Hash.blake2b(self.encode())

    @staticmethod
    def genesis(path="dev-spec.json") -> "Header":
        return Header.decode(bytes.fromhex(json.load(open(path))["genesis_header"]))

    def produce(
        self,
        time_slot: TimeSlot,
        extrinsic: Extrinsic,
        ticket: Optional[TicketEnvelope],
    ):
        """
        Produces a child header of current header
        """
        from jam.settings import settings
        from jam.state.state import state

        header = Header(
            parent=Hash.blake2b(self.encode()),
            parent_state_root=state.root,
            extrinsic_hash=Hash.blake2b(extrinsic.encode()),
            slot=time_slot,
            epoch_mark=EpochMark.produce(state, time_slot),
            tickets_mark=TicketsMark.produce(state, time_slot),
            offenders_mark=OffendersMark.produce(extrinsic.disputes),
            author_index=ValidatorIndex(state.kappa.index(settings.val)),
            entropy_source=BandersnatchVrfSignature(96),
            seal=BandersnatchVrfSignature(96),
        )

        # --- Seal --- #
        # If start of a new epoch, use eta[2], else eta[3]
        eta = state.eta[2] if time_slot % EPOCH_LENGTH == 0 else state.eta[3]

        # Fallback / Ticket context
        context = (
            X.TICKET.value + eta.encode() + ticket.attempt.encode()
            if ticket
            else X.FALLBACK.value + eta.encode()
        )
        header.seal = BandersnatchVrfSignature(
            prove_ietf(
                settings.bandersnatch_private,
                context,
                header.encode_unsigned(),
            )
        )
        header.entropy_source = BandersnatchVrfSignature(
            prove_ietf(
                settings.bandersnatch_private,
                X.ENTROPY + vrf_output(header.seal),
                b"",
            )
        )

    def validate(self) -> bool:
        """
        Validate a block's header
        1. Extrinsic hash should match hash(block.extrinsics)
        2. Valid Seal + Entropy, matching author
        3. Parent header should exist
        4. Timeslot < curr time
        5. Author index (H_i) <= V
        6. H_e only when epoch transition
        7. H_r == state.root
        """
        from jam.settings import settings
        from jam.state.state import state

        slot_entry = self.slot % EPOCH_LENGTH
        full_val_set = state.kappa

        # Author check
        if self.author_index > len(full_val_set):
            raise BlockError(BlockErrorCode.INVALID_AUTHOR)
        author = full_val_set[self.author_index]

        s_vals = state.gamma.s.unwrap()
        entry = s_vals[slot_entry]

        # Authorized sealer
        if isinstance(s_vals, GammaSFallback):
            if author.bandersnatch != s_vals[slot_entry]:
                raise BlockError(
                    BlockErrorCode.INVALID_AUTHOR,
                    f"Expected {s_vals[slot_entry]}, got {author.bandersnatch}",
                )
        else:
            if s_vals[slot_entry].id != vrf_output(self.seal):
                raise BlockError(BlockErrorCode.INVALID_AUTHOR)

        eta = state.eta[3]
        context = (
            X.TICKET.value + eta.encode() + entry.attempt.encode()
            if isinstance(s_vals, GammaSTickets)
            else X.FALLBACK.value + eta.encode()
        )
        # Verify seal
        if not verify_ietf(author.bandersnatch, self.seal, context, self.encode_unsigned()):
            raise BlockError(BlockErrorCode.INVALID_SEAL)

        # Verify entropy
        if not verify_ietf(
            author.bandersnatch, self.entropy_source, X.ENTROPY.value + vrf_output(self.seal), b""
        ):
            raise BlockError(BlockErrorCode.INVALID_ENTROPY)

        # State root check
        if self.parent_state_root != state.root:
            raise BlockError(BlockErrorCode.INCORRECT_STATE_ROOT)

        # Marker checks
        is_new_epoch = (self.slot // EPOCH_LENGTH) == (state.tau // EPOCH_LENGTH)
        # Epoch marker
        if is_new_epoch and self.epoch_mark.unwrap() is None:
            raise BlockError(BlockErrorCode.EPOCH_MARKER_EMPTY)
        elif not is_new_epoch and self.epoch_mark.unwrap() is not None:
            raise BlockError(BlockErrorCode.EPOCH_MARKER_NOT_EMPTY)

        # If we're in ticket mode
        is_ticket_mode = len(state.gamma.a) >= EPOCH_LENGTH
        if is_new_epoch and is_ticket_mode and self.tickets_mark.unwrap() is None:
            raise BlockError(BlockErrorCode.TICKETS_MARK_EMPTY)
        elif not is_new_epoch and self.tickets_mark.unwrap() is not None:
            raise BlockError(BlockErrorCode.TICKETS_MARK_NOT_EMPTY)

        # Parent exists
        if settings.main_db.get(self.parent) is None:
            if not self.parent != Bytes[32](32) and self.parent != self.genesis().hash():
                raise BlockError(
                    BlockErrorCode.INVALID_PARENT, f"Parent block not found {self.parent.hex()}"
                )

        return True
