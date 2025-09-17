from tsrkit_types.bytes import Bytes
from jam.types.state.gamma import GammaSTickets
import json
from typing import Optional, Self
from jam.block.errors import BlockError, BlockErrorCode
from jam.block.extrinsics.extrinsic import Extrinsic
from jam.types.protocol.ticket import TicketBody
from jam.types.state.gamma import GammaSFallback
from jam.utils.constants import EPOCH_LENGTH, TICKET_SUBMISSION_END, X
from tsrkit_types import Option, structure, Null
from jam.types import (
    BandersnatchVrfSignature,
    Hash,
    HeaderHash,
    StateRoot,
    OpaqueHash,
    TimeSlot,
    ValidatorIndex,
)

from .epoch_mark import EpochMark
from .offenders_mark import OffendersMark
from .tickets_mark import TicketsMark
from py_ark_vrf import prove_ietf, vrf_output, verify_ietf


@structure
class Header:
    """Block header structure."""
    # HP
    parent: HeaderHash
    # HR
    parent_state_root: StateRoot
    # HX
    extrinsic_hash: OpaqueHash
    # HT
    slot: TimeSlot
    # HE
    epoch_mark: EpochMark
    # HT    
    tickets_mark: TicketsMark
    # HA
    author_index: ValidatorIndex
    # HV
    entropy_source: BandersnatchVrfSignature
    # HO 
    offenders_mark: OffendersMark
    # HS
    seal: BandersnatchVrfSignature

    def __hash__(self) -> int:
        return int.from_bytes(self.hash())

    def encode_unsigned(self) -> bytes:
        return self.encode()[:-96]

    def hash(self) -> HeaderHash:
        return HeaderHash(Hash.blake2b(self.encode()))

    @staticmethod
    def genesis(path="dev-spec.json") -> "Header":
        return Header.decode(bytes.fromhex(json.load(open(path))["genesis_header"]))

    def produce(
        self,
        time_slot: TimeSlot,
        extrinsic: Extrinsic,
        ticket: TicketBody | None,
    ) -> Self | None:
        """
        Produces a child header of current header
        """
        from jam.settings import settings
        from jam.state.state import state 

        header = Header(
            parent=Hash.blake2b(self.encode()),
            parent_state_root=state.root,
            extrinsic_hash=extrinsic.hash(),
            slot=time_slot,
            epoch_mark=EpochMark.produce(state, time_slot),
            tickets_mark=TicketsMark.produce(state, time_slot),
            offenders_mark=OffendersMark.produce(extrinsic.disputes),
            author_index=ValidatorIndex([k.bandersnatch for k in state.kappa].index(settings.bandersnatch_public)),
            entropy_source=BandersnatchVrfSignature(96),
            seal=BandersnatchVrfSignature(96),
        )

        # --- Seal --- #
        # If start of a new epoch, use eta[2], else eta[3]
        eta = state.eta[2] if state.tau // EPOCH_LENGTH != time_slot // EPOCH_LENGTH else state.eta[3]

        # Fallback / Ticket context
        context = (
            X.TICKET.value + eta + bytes([ticket.attempt])
            if ticket
            else X.FALLBACK.value + eta.encode()
        )

        seal_output = vrf_output(
            prove_ietf(
                settings.bandersnatch_private, 
                context, b""
            )
        )
        header.entropy_source = BandersnatchVrfSignature(
            prove_ietf(
                settings.bandersnatch_private,
                X.ENTROPY.value + seal_output, b"",
            )
        )
        header.seal = BandersnatchVrfSignature(
            prove_ietf(
                settings.bandersnatch_private,
                context, header.encode_unsigned(),
            )
        )
        
        return header

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
                    BlockErrorCode.INVALID_AUTHOR, f"Expected: {s_vals[slot_entry].hex()}, Actual: {author.bandersnatch.hex()}",
                )
        else:
            if s_vals[slot_entry].id != vrf_output(self.seal):
                raise BlockError(BlockErrorCode.INVALID_AUTHOR)

        eta = state.eta[3]
        context = (
            X.TICKET.value + eta + bytes([entry.attempt])
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
            raise BlockError(BlockErrorCode.INCORRECT_STATE_ROOT, f"E: {self.parent_state_root.hex()}, A: {state.root.hex()}")
        
        from ...state.state import State
        pre_state = State.load()

        # Marker checks
        is_new_epoch = (self.slot // EPOCH_LENGTH) > (pre_state.tau // EPOCH_LENGTH)
        # Epoch marker
        if is_new_epoch and self.epoch_mark.unwrap() == Null:
            raise BlockError(BlockErrorCode.EPOCH_MARKER_EMPTY)
        elif not is_new_epoch and self.epoch_mark.unwrap() != Null:
            raise BlockError(BlockErrorCode.EPOCH_MARKER_NOT_EMPTY)

        # If we're in ticket mode
        is_ticket_mode = len(state.gamma.a) >= EPOCH_LENGTH
        is_last_ticket_slot = pre_state.tau % EPOCH_LENGTH < TICKET_SUBMISSION_END and self.slot % EPOCH_LENGTH >= TICKET_SUBMISSION_END
        if is_last_ticket_slot and is_ticket_mode and not is_new_epoch and self.tickets_mark.unwrap() == Null:
            raise BlockError(BlockErrorCode.TICKETS_MARK_EMPTY)
        if not (is_last_ticket_slot or is_ticket_mode or is_new_epoch) and self.tickets_mark.unwrap() != Null:
            print(is_new_epoch, self.tickets_mark)
            raise BlockError(BlockErrorCode.TICKETS_MARK_NOT_EMPTY)

        # Parent exists
        if settings.main_db.get(self.parent) is None:
            if not self.parent != Bytes[32](32) and self.parent != self.genesis().hash():
                raise BlockError(
                    BlockErrorCode.INVALID_PARENT, f"Parent block not found {self.parent.hex()}"
                )

        return True
